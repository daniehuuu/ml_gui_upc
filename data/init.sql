USE aldimi_db;

-- -----------------------------------------------------
-- TABLA: pacientes
-- Objetivo: Clasificación de Thyroid_Cancer_Risk
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS pacientes (
    Patient_ID VARCHAR(50) PRIMARY KEY,
    patient_code VARCHAR(50),
    patient_name VARCHAR(150),
    Age INT,
    locality VARCHAR(100),
    admission_date DATETIME,
    assigned_program VARCHAR(100),
    contact_priority VARCHAR(50),
    Gender VARCHAR(50),
    Country VARCHAR(100),
    Ethnicity VARCHAR(100),
    Family_History VARCHAR(50),
    Radiation_Exposure VARCHAR(50),
    Iodine_Deficiency VARCHAR(50),
    Smoking VARCHAR(50),
    Obesity VARCHAR(50),
    Diabetes VARCHAR(50),
    TSH_Level DOUBLE,
    T3_Level DOUBLE,
    T4_Level DOUBLE,
    Nodule_Size DOUBLE,
    Thyroid_Cancer_Risk VARCHAR(50), -- Variable objetivo
    Diagnosis VARCHAR(150)
);

-- -----------------------------------------------------
-- TABLA: inventario
-- Objetivo: Regresión de warehouse_inventory_level
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS inventario (
    -- Agregamos un ID autoincremental como buena práctica para registros logísticos
    id_registro INT AUTO_INCREMENT PRIMARY KEY, 
    resource_code VARCHAR(50),
    resource_name VARCHAR(150),
    resource_category VARCHAR(100),
    warehouse_name VARCHAR(100),
    locality VARCHAR(100),
    assigned_program VARCHAR(100),
    unit_type VARCHAR(50),
    minimum_required_stock DOUBLE,
    last_restock_date DATETIME,
    criticality_level VARCHAR(50),
    supply_status VARCHAR(50),
    logistic_recommendation VARCHAR(255),
    timestamp DATETIME,
    vehicle_gps_latitude DOUBLE,
    vehicle_gps_longitude DOUBLE,
    fuel_consumption_rate DOUBLE,
    eta_variation_hours DOUBLE,
    traffic_congestion_level VARCHAR(50),
    warehouse_inventory_level DOUBLE, -- Variable objetivo
    loading_unloading_time DOUBLE,
    handling_equipment_availability VARCHAR(50),
    order_fulfillment_status VARCHAR(50),
    weather_condition_severity VARCHAR(50),
    port_congestion_level VARCHAR(50),
    shipping_costs DOUBLE,
    supplier_reliability_score DOUBLE,
    lead_time_days DOUBLE,
    historical_demand DOUBLE,
    iot_temperature DOUBLE,
    cargo_condition_status VARCHAR(50),
    route_risk_level VARCHAR(50),
    customs_clearance_time DOUBLE,
    driver_behavior_score DOUBLE,
    fatigue_monitoring_score DOUBLE,
    disruption_likelihood_score DOUBLE,
    delay_probability DOUBLE,
    risk_classification VARCHAR(50),
    delivery_time_deviation DOUBLE
);