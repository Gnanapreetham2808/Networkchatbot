export function DataTable({ data }: { data: any[] }) {
  return (
    <table className="w-full border">
      <thead>
        <tr>{Object.keys(data[0] || {}).map((key) => <th key={key} className="border px-2 py-1">{key}</th>)}</tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            {Object.values(row).map((val, j) => (
              <td key={j} className="border px-2 py-1">{String(val)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
