CREATE DATABASE sales_intelligence_hub;

USE sales_intelligence_hub;

CREATE TABLE branches (
    Branch_Id INT PRIMARY KEY AUTO_INCREMENT,
    Branch_Name VARCHAR(100) NOT NULL,
    Branch_Admin_Name VARCHAR(100) NOT NULL
);
INSERT INTO branches(Branch_Name, Branch_Admin_Name) VALUES
('Chennai', 'Murugan'),
('Madurai', 'Ayyanar'),
('Thanjavur', 'Eswaran'),
('Trichy', 'Srinivasan'),
('Salem', 'Sanmugam');
CREATE TABLE sales (
    Sale_Id INT AUTO_INCREMENT PRIMARY KEY,
    Branch_Id INT NOT NULL,
    Date DATE NOT NULL,
    Name VARCHAR(255) NOT NULL,
    Mobile_Number VARCHAR(15),
    Product_Name ENUM('DS','DA','BA','FSD') NOT NULL,
    Gross_Sales DECIMAL(12,2) NOT NULL,
    Received_Amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    Pending_Amount DECIMAL(12,2) AS (gross_sales - received_amount) STORED,
    Status ENUM('Open','Close') NOT NULL DEFAULT 'Open',
    CONSTRAINT fk_branch
        FOREIGN KEY (Branch_Id) REFERENCES branches(Branch_Id)
	);
INSERT INTO sales (Branch_Id, Date, Name, Mobile_Number, Product_Name, Gross_Sales, Received_Amount, Status)
VALUES
((SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1), '2026-03-23', 'Rahul', '9876543210', 'DS', 5000.00, 2000.00, 'Open'),
((SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 1), '2026-03-22', 'Kathir', '9123456780', 'DA', 7500.50, 7500.50, 'Close'),
((SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 2), '2026-03-21', 'Roshan', '9988776655', 'BA', 3000.00, 1000.00, 'Open'),
((SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 3), '2026-03-20', 'Raja', '9012345678', 'FSD', 12000.00, 12000.00, 'Close'),
((SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 4), '2026-03-19', 'Kavilan', '9098765432', 'DS', 6500.00, 4000.00, 'Open');

CREATE TABLE users (
    User_Id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    Branch_Id INT,
    Role ENUM('Super Admin', 'Admin') NOT NULL,
Email VARCHAR(255) UNIQUE NOT NULL,
    FOREIGN KEY (Branch_Id) REFERENCES branches(Branch_Id)
);
INSERT INTO users (username, password, Branch_Id, Role, Email)
VALUES
('murugan_super', 'password123', NULL, 'Super Admin', 'murugan@example.com'),
('ayyanar_admin', 'password123', (SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 1), 'Admin', 'ayyanar@example.com'),
('eswaran_admin', 'password123', (SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 2), 'Admin', 'eswaran@example.com'),
('srinivasan_admin', 'password123', (SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 3), 'Admin', 'srinivasan@example.com'),
('sanmugam_adim', 'password123', (SELECT Branch_Id FROM branches ORDER BY Branch_Id LIMIT 1 OFFSET 4), 'Admin', 'sanmugam@example.com');
CREATE TABLE payment_splits (
    Payment_I INT AUTO_INCREMENT PRIMARY KEY,
    Sale_Id INT NOT NULL,
    Payment_Date DATE NOT NULL,
    Amount_Paid DECIMAL(12,2) NOT NULL,
    Payment_Method VARCHAR(50) NOT NULL,
    CONSTRAINT fk_sale
        FOREIGN KEY (Sale_Id) 
        REFERENCES sales(Sale_Id)
);
INSERT INTO payment_splits (Sale_Id, Payment_Date, Amount_Paid, Payment_Method)
VALUES
(6, '2026-03-25', 3000.00, 'Cash');
SELECT * FROM branches ;
SELECT * FROM users;
SELECT * FROM sales;
SELECT * FROM payment_splits;

-- Drop the trigger if it exists
DROP TRIGGER IF EXISTS after_payment_insert;

DELIMITER $$

CREATE TRIGGER after_payment_insert
AFTER INSERT ON payment_splits
FOR EACH ROW
BEGIN
    DECLARE total_received DECIMAL(12,2);
    DECLARE gross_amount DECIMAL(12,2);

    -- Calculate total received amount for this sale
    SELECT SUM(Amount_Paid) INTO total_received
    FROM payment_splits
    WHERE Sale_Id = NEW.Sale_Id;

    -- Get Gross Sales amount for this sale
    SELECT Gross_Sales INTO gross_amount
    FROM sales
    WHERE Sale_Id = NEW.Sale_Id;

    -- Update the sales table
    UPDATE sales
    SET 
        Received_Amount = total_received,
        Pending_Amount = gross_amount - total_received,
        Status = CASE 
                     WHEN total_received >= gross_amount THEN 'Close'
                     ELSE 'Open'
                 END
    WHERE Sale_Id = NEW.Sale_Id;
END$$

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE payment_splits;
TRUNCATE TABLE sales;
TRUNCATE TABLE users;
TRUNCATE TABLE branches;

SET FOREIGN_KEY_CHECKS = 1;

ALTER TABLE sales 
DROP COLUMN Pending_Amount;

ALTER TABLE sales 
ADD Pending_Amount DECIMAL(12,2);

select *from sales;
select*from branches;
select*from users;
select*from payment_splits;
delete from payment_splits;
delete from sales;
delete from users;
delete from branches;
SELECT COUNT(*) FROM sales;
ALTER TABLE sales
MODIFY Product_Name ENUM('DS','DA','BA','FSD','BI','SQL','ML','AI') NOT NULL;