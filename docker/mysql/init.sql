-- MySQL initialization script
-- This script sets up the database with proper character set and collation

-- Set character set and collation
ALTER DATABASE goals CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Set timezone
SET time_zone = '+00:00';

-- Set SQL mode for strict data validation
SET sql_mode = 'STRICT_ALL_TABLES';

-- Create the goals database if it doesn't exist
CREATE DATABASE IF NOT EXISTS goals CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the goals database
USE goals;

-- Grant privileges to the goals user
GRANT ALL PRIVILEGES ON goals.* TO 'goals'@'%';
FLUSH PRIVILEGES;
