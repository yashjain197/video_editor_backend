CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    duration FLOAT,
    size INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    result_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    metadata JSONB
);
CREATE TABLE IF NOT EXISTS trimmed_videos (
    id SERIAL PRIMARY KEY,
    original_video_id INTEGER REFERENCES videos(id) NOT NULL,
    trimmed_filename VARCHAR(255) NOT NULL,
    start FLOAT NOT NULL,
    end FLOAT NOT NULL,
    duration FLOAT,
    size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS overlay_configs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(36) REFERENCES jobs(job_id) NOT NULL,
    video_id INTEGER REFERENCES videos(id) NOT NULL,
    config JSONB NOT NULL,
    output_filename VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
