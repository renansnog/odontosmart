-- Execute uma vez na estrutura anterior, após backup e com o aplicativo parado.
USE clinica_oblanco;

CREATE TABLE IF NOT EXISTS dentistas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cro VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- A coluna de referência precisa herdar a codificação do CPF no banco anterior.
SELECT CHARACTER_SET_NAME, COLLATION_NAME INTO @cpf_charset, @cpf_collation
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pacientes' AND COLUMN_NAME = 'id_CPF';

SET @alterar = CONCAT(
    'ALTER TABLE consultas ADD COLUMN paciente_cpf VARCHAR(11) CHARACTER SET ',
    @cpf_charset, ' COLLATE ', @cpf_collation,
    ', ADD COLUMN dentista_id INT',
    ", ADD COLUMN status ENUM('Agendada', 'Realizada', 'Cancelada') NOT NULL DEFAULT 'Agendada'",
    ", ADD COLUMN dentista_horario INT GENERATED ALWAYS AS (CASE WHEN status <> 'Cancelada' THEN dentista_id END) STORED",
    ', ADD UNIQUE KEY uq_consulta_horario (dentista_horario, data_consulta, horario)',
    ', ADD CONSTRAINT fk_consulta_paciente FOREIGN KEY (paciente_cpf) REFERENCES pacientes(id_CPF) ON UPDATE CASCADE',
    ', ADD CONSTRAINT fk_consulta_dentista FOREIGN KEY (dentista_id) REFERENCES dentistas(id)'
);
PREPARE adicionar_colunas FROM @alterar;
EXECUTE adicionar_colunas;
DEALLOCATE PREPARE adicionar_colunas;

-- Quando houver mais de um paciente por consulta, mantenha os vínculos originais
-- em pacientes.id_Consulta para revisão manual e deixe o novo campo em branco.
UPDATE consultas AS c
JOIN (
    SELECT id_Consulta, MIN(id_CPF) AS cpf
    FROM pacientes
    WHERE id_Consulta IS NOT NULL
    GROUP BY id_Consulta
    HAVING COUNT(*) = 1
) AS vinculo ON c.id_Consulta = vinculo.id_Consulta
SET c.paciente_cpf = vinculo.cpf;
