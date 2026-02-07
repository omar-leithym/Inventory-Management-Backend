import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Line, ComposedChart, Legend } from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div style={{
      background: 'white',
      padding: '10px 14px',
      borderRadius: 8,
      boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
      border: '1px solid #E0E0E0'
    }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
      {data.actual !== null && (
        <div style={{ color: '#1B5E20', display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#1B5E20' }}></span>
          Actual: {data.actual}
        </div>
      )}
      <div style={{ color: '#FF8F00', display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 8, height: 2, background: '#FF8F00' }}></span>
        Predicted: {data.predicted}
      </div>
    </div>
  );
}

function CustomLegend() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#1B5E20' }}></span>
        <span style={{ color: '#1B5E20', fontWeight: 500 }}>Actual</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 12, height: 2, background: '#FF8F00' }}></span>
        <span style={{ color: '#FF8F00', fontWeight: 500 }}>Predicted</span>
      </div>
    </div>
  );
}

export default function DemandChart({ data = [] }) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1B5E20" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#1B5E20" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E0E0E0" />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: '#666' }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: '#666' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="actual"
            stroke="#1B5E20"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#gradActual)"
            dot={{ r: 4, fill: '#1B5E20', strokeWidth: 0 }}
            connectNulls={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#FF8F00"
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <CustomLegend />
    </div>
  );
}
