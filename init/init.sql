CREATE TABLE IF NOT EXISTS users (
    user_idx INT AUTO_INCREMENT PRIMARY KEY,
    id VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    username VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    gender ENUM('w','m'),
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role ENUM('user', 'admin')
);

CREATE TABLE IF NOT EXISTS ai_malbeot_logs (
    log_idx INT AUTO_INCREMENT PRIMARY KEY,
    user_idx INT NOT NULL,
    session_id INT NOT NULL,
    speaker ENUM('user', 'model') NOT NULL,
    chat_text TEXT NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_idx) REFERENCES users(user_idx)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS video_logs (
    video_id VARCHAR(100) PRIMARY KEY,
    user_id INT NOT NULL,
    script TEXT,
    status ENUM('pending', 'done', 'failed') DEFAULT 'pending',
    video_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_idx) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS practice_logs (
    practice_idx INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    practice_text TEXT NOT NULL,
    converted_text TEXT NOT NULL,
    video_id VARCHAR(100),
    score INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_idx),
    FOREIGN KEY (video_id) REFERENCES video_logs(video_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pronunciation_logs (
    pronunciation_id VARCHAR(100) PRIMARY KEY,
    user_id INT NOT NULL,
    reference_text TEXT NOT NULL,
    recognized_text TEXT NOT NULL,
    accuracy_score FLOAT NOT NULL,
    fluency_score FLOAT NOT NULL,
    completeness_score FLOAT NOT NULL,
    phoneme_scores JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_idx) ON DELETE CASCADE
);

INSERT INTO users (id, password, username, email, gender, join_date, role)
VALUES('testuser123', '$2b$12$F5mfLpLS7SN7dzDI.DCJ/.jJZ5Lw00wqbYCxSmv8IJZB9Jz3nlB0a', '테스트', 'test@gmail.com', 'W', CURRENT_TIMESTAMP, 'user');