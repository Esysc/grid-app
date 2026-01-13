import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

const PowerQualityChart = ({ data, dataKey, yAxisLabel, color }) => {
  // Handle empty or undefined data
  if (!Array.isArray(data)) {
    return <div>No data available</div>;
  }
  
  // Keep only last 30 data points to avoid axis jitter
  const recentData = data.slice(-30);
  
  // Format timestamp for display - use fixed time format to avoid re-renders
  const formatData = React.useMemo(() => 
    recentData.map(item => ({
      ...item,
      time: new Date(item.timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: false 
      })
    })), 
    [recentData.length, recentData[recentData.length - 1]?.timestamp]
  );

  // Define thresholds based on data type
  const getThreshold = () => {
    if (dataKey === 'voltage') return { value: 240, label: 'Nominal' };
    if (dataKey === 'thd') return { value: 5, label: 'Warning' };
    return null;
  };

  const threshold = getThreshold();

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={formatData}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis 
          dataKey="time" 
          stroke="#a0aec0"
          style={{ fontSize: '12px' }}
          tick={{ fontSize: 12 }}
          interval={Math.max(0, Math.floor(formatData.length / 6))}
        />
        <YAxis 
          stroke="#a0aec0"
          label={{ value: yAxisLabel, angle: -90, position: 'insideLeft', fill: '#a0aec0' }}
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '5px',
            color: '#fff'
          }}
        />
        <Legend 
          wrapperStyle={{ color: '#a0aec0' }}
        />
        {threshold && (
          <ReferenceLine 
            y={threshold.value} 
            label={threshold.label}
            stroke="red" 
            strokeDasharray="3 3"
          />
        )}
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PowerQualityChart;
