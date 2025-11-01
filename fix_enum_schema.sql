-- Fix enum columns: Convert MySQL ENUM to VARCHAR
-- Run this script directly on MySQL to fix the schema

USE goals;

-- Convert goal_type enum to varchar
ALTER TABLE goals MODIFY COLUMN goal_type VARCHAR(20) NOT NULL;

-- Convert timeframe_type enum to varchar
ALTER TABLE goals MODIFY COLUMN timeframe_type VARCHAR(20) NOT NULL;

-- Convert privacy enum to varchar
ALTER TABLE goals MODIFY COLUMN privacy VARCHAR(20) NOT NULL;

-- Convert status enum to varchar
ALTER TABLE goals MODIFY COLUMN status VARCHAR(20) NOT NULL;

-- Convert role enum to varchar (goal_members table)
ALTER TABLE goal_members MODIFY COLUMN role VARCHAR(20) NOT NULL;

-- Verify the changes
DESCRIBE goals;
DESCRIBE goal_members;

