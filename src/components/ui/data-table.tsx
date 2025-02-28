import React from 'react';

interface DataTableProps<T extends object> {
  data: T[];
  columns: {
    key: keyof T | string;
    title: string;
    render?: (item: T) => React.ReactNode;
  }[];
  searchable?: boolean;
  onRowClick?: (item: T) => void;
}

function DataTable<T extends object>({ data, columns, searchable, onRowClick }: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = React.useState('');

  const filteredData = searchable
    ? data.filter(item =>
        columns.some(column => {
          if (typeof column.key !== 'string' && column.key in item) {
            return String(item[column.key as keyof T]).toLowerCase().includes(searchTerm.toLowerCase());
          }
          return false;
        })
      )
    : data;

  return (
    <div>
      {searchable && (
        <input
          type="text"
          placeholder="Search..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          className="mb-4 p-2 border rounded"
        />
      )}
      <table className="min-w-full bg-white">
        <thead>
          <tr>
            {columns.map(column => (
              <th key={String(column.key)} className="py-2 px-4 border-b">
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filteredData.map((item, index) => (
            <tr
              key={index}
              onClick={() => onRowClick && onRowClick(item)}
              className="cursor-pointer hover:bg-gray-100"
            >
              {columns.map(column => (
                <td key={String(column.key)} className="py-2 px-4 border-b">
                  {column.render ? column.render(item) : (typeof column.key !== 'string' ? String(item[column.key]) : '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable; 