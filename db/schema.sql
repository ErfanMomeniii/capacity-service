DROP TABLE IF EXISTS sailings CASCADE;

CREATE TABLE sailings (
    id SERIAL PRIMARY KEY,
    service_version_and_roundtrip_identfiers TEXT NOT NULL,
    origin_service_version_and_master TEXT NOT NULL,
    destination_service_version_and_master TEXT NOT NULL,
    vessel_identifier TEXT NOT NULL,
    origin_port_code TEXT,
    destination_port_code TEXT,
    origin_at_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    offered_capacity_teu INTEGER NOT NULL CHECK (offered_capacity_teu >= 0)
);

-- Indexes for common filters
CREATE INDEX idx_sailings_origin_date
    ON sailings (origin_service_version_and_master, destination_service_version_and_master, origin_at_utc);

CREATE INDEX idx_sailings_vessel
    ON sailings (service_version_and_roundtrip_identfiers, vessel_identifier);
