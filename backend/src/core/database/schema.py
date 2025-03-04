from typing import Dict, List, Optional, Any, Type
from enum import Enum
import json
from pydantic import BaseModel, Field
from ..base import BaseComponent
from ..utils.errors import handle_errors

class ColumnType(str, Enum):
    """Database column types"""
    INTEGER = 'INTEGER'
    BIGINT = 'BIGINT'
    FLOAT = 'FLOAT'
    DECIMAL = 'DECIMAL'
    VARCHAR = 'VARCHAR'
    TEXT = 'TEXT'
    BOOLEAN = 'BOOLEAN'
    DATE = 'DATE'
    TIMESTAMP = 'TIMESTAMP'
    JSON = 'JSON'
    JSONB = 'JSONB'
    UUID = 'UUID'

class Column(BaseModel):
    """Database column definition"""
    name: str
    type: ColumnType
    length: Optional[int] = None
    nullable: bool = True
    default: Optional[Any] = None
    primary_key: bool = False
    unique: bool = False
    index: bool = False
    foreign_key: Optional[str] = None
    description: Optional[str] = None

class Table(BaseModel):
    """Database table definition"""
    name: str
    columns: List[Column]
    indexes: Optional[List[Dict]] = None
    constraints: Optional[List[Dict]] = None
    description: Optional[str] = None

class SchemaManager(BaseComponent):
    """Database schema management system"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self._tables: Dict[str, Table] = {}
        self._models: Dict[str, Type[BaseModel]] = {}

    async def initialize(self) -> None:
        """Initialize schema manager"""
        pass

    async def cleanup(self) -> None:
        """Cleanup schema resources"""
        self._tables.clear()
        self._models.clear()

    def register_table(self, table: Table) -> None:
        """Register table definition"""
        self._tables[table.name] = table
        
        # Generate Pydantic model
        model = self._generate_model(table)
        self._models[table.name] = model

    def get_table(self, name: str) -> Optional[Table]:
        """Get table definition"""
        return self._tables.get(name)

    def get_model(self, name: str) -> Optional[Type[BaseModel]]:
        """Get table model"""
        return self._models.get(name)

    @handle_errors(logger=None)
    async def create_table(self, table: Table) -> None:
        """Create database table"""
        db = self.app.get_component('database')
        if not db:
            self.logger.error("Database component not available")
            raise RuntimeError("Database component not available")

        query = self._generate_create_table(table)

        async with db.transaction():
            try:
                await db.execute(query)
                self.logger.info(f"Table '{table.name}' created successfully.")

                if table.indexes:
                    for index in table.indexes:
                        await db.execute(self._generate_create_index(table.name, index))
                        self.logger.info(f"Index created for table '{table.name}'.")

                self.register_table(table)
            except Exception as e:
                self.logger.error(f"Failed to create table '{table.name}': {str(e)}")
                raise

    @handle_errors(logger=None)
    async def drop_table(self, name: str) -> None:
        """Drop database table"""
        db = self.app.get_component('database')
        if not db:
            raise RuntimeError("Database component not available")
            
        await db.execute(f"DROP TABLE IF EXISTS {name} CASCADE")
        
        if name in self._tables:
            del self._tables[name]
        if name in self._models:
            del self._models[name]

    def _generate_model(self, table: Table) -> Type[BaseModel]:
        """Generate Pydantic model from table definition"""
        fields = {}
        
        for column in table.columns:
            python_type = self._get_python_type(column.type)
            
            field = (
                python_type if column.nullable
                else python_type
            )
            
            fields[column.name] = (
                field,
                Field(
                    default=column.default if column.nullable else ...,
                    description=column.description
                )
            )
            
        model_name = ''.join(
            word.capitalize()
            for word in table.name.split('_')
        )
        
        return type(
            model_name,
            (BaseModel,),
            {
                '__annotations__': fields,
                '__doc__': table.description
            }
        )

    def _generate_create_table(self, table: Table) -> str:
        """Generate CREATE TABLE query"""
        columns = []
        
        for column in table.columns:
            definition = [
                column.name,
                self._get_sql_type(column)
            ]
            
            if not column.nullable:
                definition.append('NOT NULL')
                
            if column.default is not None:
                definition.append(f"DEFAULT {self._format_default(column.default)}")
                
            if column.primary_key:
                definition.append('PRIMARY KEY')
                
            if column.unique:
                definition.append('UNIQUE')
                
            if column.foreign_key:
                definition.append(f"REFERENCES {column.foreign_key}")
                
            columns.append(' '.join(definition))
            
        # Add constraints
        if table.constraints:
            for constraint in table.constraints:
                columns.append(self._format_constraint(constraint))
                
        query = f"""
            CREATE TABLE {table.name} (
                {',\n    '.join(columns)}
            )
        """
        
        return query

    def _generate_create_index(self,
                             table_name: str,
                             index: Dict) -> str:
        """Generate CREATE INDEX query"""
        index_name = index.get('name', f"{table_name}_{index['columns']}_idx")
        columns = ', '.join(index['columns'])
        unique = 'UNIQUE ' if index.get('unique') else ''
        
        return f"""
            CREATE {unique}INDEX {index_name}
            ON {table_name} ({columns})
        """

    def _get_sql_type(self, column: Column) -> str:
        """Get SQL type definition"""
        sql_type = column.type.value
        
        if column.length and column.type in [
            ColumnType.VARCHAR,
            ColumnType.DECIMAL
        ]:
            sql_type = f"{sql_type}({column.length})"
            
        return sql_type

    def _get_python_type(self, column_type: ColumnType) -> Type:
        """Get Python type for column"""
        type_map = {
            ColumnType.INTEGER: int,
            ColumnType.BIGINT: int,
            ColumnType.FLOAT: float,
            ColumnType.DECIMAL: float,
            ColumnType.VARCHAR: str,
            ColumnType.TEXT: str,
            ColumnType.BOOLEAN: bool,
            ColumnType.DATE: str,
            ColumnType.TIMESTAMP: str,
            ColumnType.JSON: dict,
            ColumnType.JSONB: dict,
            ColumnType.UUID: str
        }
        
        return type_map.get(column_type, Any)

    def _format_default(self, value: Any) -> str:
        """Format default value for SQL"""
        if value is None:
            return 'NULL'
        elif isinstance(value, bool):
            return str(value).upper()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (dict, list)):
            return f"'{json.dumps(value)}'"
        else:
            return f"'{value}'"

    def _format_constraint(self, constraint: Dict) -> str:
        """Format table constraint"""
        if constraint['type'] == 'CHECK':
            return f"CHECK ({constraint['condition']})"
        elif constraint['type'] == 'FOREIGN KEY':
            columns = ', '.join(constraint['columns'])
            references = constraint['references']
            return f"FOREIGN KEY ({columns}) REFERENCES {references}"
        elif constraint['type'] == 'UNIQUE':
            columns = ', '.join(constraint['columns'])
            return f"UNIQUE ({columns})"
        else:
            raise ValueError(f"Unknown constraint type: {constraint['type']}") 