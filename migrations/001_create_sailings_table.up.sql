CREATE TABLE sailings (
    id SERIAL PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    origin_port_code TEXT NOT NULL,
    destination_port_code TEXT NOT NULL,
    service_version_and_roundtrip_identfiers TEXT NOT NULL,
    origin_service_version_and_master TEXT NOT NULL,
    destination_service_version_and_master TEXT NOT NULL,
    origin_at_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    offered_capacity_teu INTEGER NOT NULL CHECK (offered_capacity_teu >= 0)
);

CREATE INDEX idx_sailings_origin_destination
    ON sailings (origin, destination);

CREATE INDEX idx_sailings_origin_date
    ON sailings (origin_at_utc);
