CREATE DATABASE IF NOT EXISTS clinica_oblanco CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE clinica_oblanco;

CREATE TABLE IF NOT EXISTS pacientes (
    id_CPF VARCHAR(11) PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(255),
    telefone VARCHAR(20),
    data_de_nascimento DATE,
    pcd ENUM('Sim', 'Não') NOT NULL DEFAULT 'Não'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dentistas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cro VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS consultas (
    id_Consulta INT AUTO_INCREMENT PRIMARY KEY,
    data_consulta DATE NOT NULL,
    horario TIME NOT NULL,
    descricao TEXT,
    paciente_cpf VARCHAR(11),
    dentista_id INT,
    status ENUM('Agendada', 'Realizada', 'Cancelada') NOT NULL DEFAULT 'Agendada',
    dentista_horario INT GENERATED ALWAYS AS (
        CASE WHEN status <> 'Cancelada' THEN dentista_id END
    ) STORED,
    UNIQUE KEY uq_consulta_horario (dentista_horario, data_consulta, horario),
    CONSTRAINT fk_consulta_paciente FOREIGN KEY (paciente_cpf)
        REFERENCES pacientes(id_CPF) ON UPDATE CASCADE,
    CONSTRAINT fk_consulta_dentista FOREIGN KEY (dentista_id) REFERENCES dentistas(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS administradores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nome VARCHAR(100),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
