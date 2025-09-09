import os
import logging
from retry import retry
from neo4j import GraphDatabase

# Load environment variables (Docker will provide these)
HOSPITALS_CSV_PATH = os.getenv("HOSPITALS_CSV_PATH")
PAYERS_CSV_PATH = os.getenv("PAYERS_CSV_PATH")
PHYSICIANS_CSV_PATH = os.getenv("PHYSICIANS_CSV_PATH")
PATIENTS_CSV_PATH = os.getenv("PATIENTS_CSV_PATH")
VISITS_CSV_PATH = os.getenv("VISITS_CSV_PATH")
REVIEWS_CSV_PATH = os.getenv("REVIEWS_CSV_PATH")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOGGER = logging.getLogger(__name__)

NODES = ["Hospital", "Payer", "Physician", "Patient", "Visit", "Review"]

def _set_uniqueness_constraints(tx, node):
    query = f"""CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node})
        REQUIRE n.id IS UNIQUE;"""
    _ = tx.run(query, {})

@retry(tries=3, delay=10)
def load_hospital_graph_from_csv() -> None:
    """Load structured hospital CSV data following
    a specific ontology into Neo4j"""
    driver = GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    LOGGER.info("Setting uniqueness constraints on nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        for node in NODES:
            session.execute_write(_set_uniqueness_constraints, node)

    # Hospital nodes
    LOGGER.info("Loading hospital nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{HOSPITALS_CSV_PATH}' AS hospitals
        MERGE (h:Hospital {{id: toInteger(hospitals.hospital_id),
                            name: hospitals.hospital_name,
                            state_name: hospitals.hospital_state}});
        """
        _ = session.run(query, {})

    # Payer nodes
    LOGGER.info("Loading payer nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{PAYERS_CSV_PATH}' AS payers
        MERGE (p:Payer {{id: toInteger(payers.payer_id),
                        name: payers.payer_name}});
        """
        _ = session.run(query, {})

    # Physician nodes
    LOGGER.info("Loading physician nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{PHYSICIANS_CSV_PATH}' AS physicians
        MERGE (p:Physician {{id: toInteger(physicians.physician_id),
                            name: physicians.physician_name,
                            dob: physicians.physician_dob,
                            grad_year: physicians.physician_grad_year,
                            school: physicians.medical_school}});
        """
        _ = session.run(query, {})

    # Patient nodes
    LOGGER.info("Loading patient nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{PATIENTS_CSV_PATH}' AS patients
        MERGE (p:Patient {{id: toInteger(patients.patient_id),
                        name: patients.patient_name,
                        sex: patients.patient_sex,
                        dob: patients.patient_dob,
                        blood_type: patients.patient_blood_type}});
        """
        _ = session.run(query, {})

    # Visit nodes
    LOGGER.info("Loading visit nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{VISITS_CSV_PATH}' AS visits
        MERGE (v:Visit {{id: toInteger(visits.visit_id)}})
        SET
          v.room_number = toInteger(visits.room_number),
          v.admission_type = visits.admission_type,
          v.admission_date = visits.date_of_admission,
          v.test_results = visits.test_results,
          v.chief_complaint = visits.chief_complaint,
          v.treatment_description = visits.treatment_description,
          v.primary_diagnosis = visits.primary_diagnosis,
          v.discharge_date = visits.discharge_date,
          v.status = visits.visit_status
        """
        _ = session.run(query, {})

    # Review nodes
    LOGGER.info("Loading review nodes")
    with driver.session(database=NEO4J_DATABASE) as session:
        query = f"""
        LOAD CSV WITH HEADERS
        FROM '{REVIEWS_CSV_PATH}' AS reviews
        MERGE (r:Review {{id: toInteger(reviews.review_id),
                        physician_name: reviews.physician_name,
                        hospital_name: reviews.hospital_name,
                        patient_name: reviews.patient_name,
                        text: reviews.review}});
        """
        _ = session.run(query, {})

    LOGGER.info("Finished loading nodes")
    LOGGER.info("Loading relationships")

    # Relationships
    with driver.session(database=NEO4J_DATABASE) as session:
        queries = [
            f"""
            LOAD CSV WITH HEADERS
            FROM '{VISITS_CSV_PATH}' AS visit
            MATCH (p:Patient {{id: toInteger(visit.patient_id)}})
            MATCH (v:Visit {{id: toInteger(visit.visit_id)}})
            MERGE (p)-[r:HAS]->(v);
            """,
            f"""
            LOAD CSV WITH HEADERS
            FROM '{VISITS_CSV_PATH}' AS visit
            MATCH (v:Visit {{id: toInteger(visit.visit_id)}})
            MATCH (h:Hospital {{id: toInteger(visit.hospital_id)}})
            MERGE (v)-[r:AT]->(h);
            """,
            f"""
            LOAD CSV WITH HEADERS
            FROM '{VISITS_CSV_PATH}' AS visit
            MATCH (v:Visit {{id: toInteger(visit.visit_id)}})
            MATCH (p:Physician {{id: toInteger(visit.physician_id)}})
            MERGE (p)-[r:TREATS]->(v);
            """,
            # --- THIS IS THE SECOND CORRECTED SECTION FOR RELATIONSHIPS ---
            f"""
            LOAD CSV WITH HEADERS
            FROM '{VISITS_CSV_PATH}' AS visit
            MATCH (v:Visit {{id: toInteger(visit.visit_id)}})
            MATCH (p:Payer {{id: toInteger(visit.payer_id)}})
            MERGE (v)-[r:COVERED_BY]->(p)
            SET r.service_date = visit.discharge_date,
                r.billing_amount = toFloat(visit.billing_amount)
            """,
            f"""
            LOAD CSV WITH HEADERS
            FROM '{REVIEWS_CSV_PATH}' AS review
            MATCH (v:Visit {{id: toInteger(review.visit_id)}})
            MATCH (r:Review {{id: toInteger(review.review_id)}})
            MERGE (v)-[rel:WRITES]->(r);
            """,
            f"""
            MATCH (p:Physician)
            MATCH (h:Hospital)
            WHERE (p.id + h.id) % 30 = 0
            MERGE (p)-[r:EMPLOYS]->(h);
            """,
        ]
        for query in queries:
            _ = session.run(query, {})

    LOGGER.info("Finished loading relationships")
    driver.close()

if __name__ == "__main__":
    load_hospital_graph_from_csv()

