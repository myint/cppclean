
-- Keep very normalized data, so that we don't ever have to do string
-- comparisons which are more costly and take up more space.
-- All filenames and identifiers are stored once in these tables.
-- All other uses of them are through foreign key references.

CREATE TABLE IF NOT EXISTS path(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(255) COLLATE latin1_bin NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS identifier(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) COLLATE latin1_bin NOT NULL UNIQUE
);

-- There are two or three tables per type of identifier stored.
-- There is always a decl(aration) table.  This table contains
-- the initial declaration of the identifier.  If there is no
-- actual declaration, one will be made and the file/line will
-- be the same as the definition.

-- Most identifiers also have a definition in addition to a decl.
-- Some identifier types are special and don't have a separate
-- declaration and definition, e.g., typedefs, enums, and fields.

-- The third type of identifier table stores the uses of it.

-- With this mechanism, it is fairly easy to find interesting properties.
-- For example, unused identifiers, identifiers without a definition
-- or declaration.  We can further constrain the searches by location,
-- name, type, etc.

-- namespace should be the only foreign key that is NULLable.

CREATE TABLE IF NOT EXISTS typedef_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        namespace INT REFERENCES identifier(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS typedef_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES typedef_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- TODO(nnorwitz): keep the values and where they are used.
CREATE TABLE IF NOT EXISTS enum_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        namespace INT REFERENCES identifier(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS enum_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES enum_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS global_variable_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        namespace INT REFERENCES identifier(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- declaration must be NULLable here because it's possible to have
-- extern int global_variable;  If global_variable is never used,
-- this will compile fine and is something we want to find.

CREATE TABLE IF NOT EXISTS global_variable_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT REFERENCES global_variable_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- modifiers are: static
CREATE TABLE IF NOT EXISTS function_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        namespace INT REFERENCES identifier(id),
        modifiers INT NOT NULL,
        num_parameters INT NOT NULL,
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS function_definition(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES function_decl(id),
        num_lines INT NOT NULL,
        complexity INT NOT NULL,
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS function_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES function_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- The class tables include structs.
CREATE TABLE IF NOT EXISTS class_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        namespace INT REFERENCES identifier(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS class_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES class_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- modifiers are: static
CREATE TABLE IF NOT EXISTS field_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        class INT NOT NULL REFERENCES class_decl(id),
        modifiers INT NOT NULL,
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS field_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES field_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

-- modifiers are: static, const
CREATE TABLE IF NOT EXISTS method_decl(
        id INT PRIMARY KEY AUTO_INCREMENT,
        name INT NOT NULL REFERENCES identifier(id),
        class INT NOT NULL REFERENCES class_decl(id),
        modifiers INT NOT NULL,
        num_parameters INT NOT NULL,
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS method_definition(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES method_decl(id),
        num_lines INT NOT NULL,
        complexity INT NOT NULL,
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);

CREATE TABLE IF NOT EXISTS method_uses(
        id INT PRIMARY KEY AUTO_INCREMENT,
        declaration INT NOT NULL REFERENCES method_decl(id),
        filename INT NOT NULL REFERENCES path(id),
        line INT NOT NULL
);
