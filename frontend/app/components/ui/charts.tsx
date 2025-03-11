import * as React from "react"
import {
  LineChart as RechartsLineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from "recharts"

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"]

interface ChartProps {
  data: any[]
  xField?: string
  yField?: string
  width?: number
  height?: number
}

export function LineChart({ data, xField = "name", yField = "value", width = 500, height = 300 }: ChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xField} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey={yField} stroke="#8884d8" />
      </RechartsLineChart>
    </ResponsiveContainer>
  )
}

export function BarChart({ data, xField = "name", yField = "value", width = 500, height = 300 }: ChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xField} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey={yField} fill="#8884d8" />
      </RechartsBarChart>
    </ResponsiveContainer>
  )
}

interface PieChartProps extends ChartProps {
  angleField?: string;
  colorField?: string;
}

export function PieChart({
  data,
  width = 400,
  height = 300,
  angleField = "value",
  colorField = "name"
}: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart
        data={data}
        width={width}
        height={height}
      >
        <Pie
          data={data}
          dataKey={angleField}
          nameKey={colorField}
          cx="50%"
          cy="50%"
          outerRadius={80}
          fill="#8884d8"
          label
        />
        <Tooltip />
        <Legend />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
} 