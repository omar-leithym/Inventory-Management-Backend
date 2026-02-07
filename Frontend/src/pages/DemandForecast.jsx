import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Grid, Chip, Autocomplete, TextField, ToggleButton, ToggleButtonGroup, Avatar, Stack } from '@mui/material';
import { alpha } from '@mui/material/styles';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import VerifiedIcon from '@mui/icons-material/Verified';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import InventoryIcon from '@mui/icons-material/Inventory2';
import PageWrapper from '../components/layout/PageWrapper';
import DemandChart from '../components/charts/DemandChart';
import mockForecast from '../mocks/forecastData.json';

export default function DemandForecast() {
  const [selectedItem, setSelectedItem] = useState(mockForecast.items[0]);
  const [granularity, setGranularity] = useState('Daily');

  return (
    <PageWrapper>
      {/* Header Banner */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1B5E20 0%, #43A047 100%)', color: 'white', border: 'none' }}>
        <CardContent sx={{ p: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: alpha('#fff', 0.2), width: 48, height: 48 }}>
                <TrendingUpIcon />
              </Avatar>
              <Box>
                <Typography variant="h5" fontWeight={800}>AI Demand Forecasting</Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Predict daily, weekly & monthly demand to optimise stock levels and reduce waste.
                </Typography>
              </Box>
            </Box>
            <Chip
              icon={<VerifiedIcon sx={{ color: 'white !important' }} />}
              label={`Model: ${mockForecast.modelName}`}
              sx={{ bgcolor: alpha('#fff', 0.2), color: 'white', fontWeight: 500 }}
            />
          </Stack>
        </CardContent>
      </Card>

      {/* Controls */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap', alignItems: 'center' }}>
        <Autocomplete
          options={mockForecast.items}
          getOptionLabel={(o) => o.name}
          value={selectedItem}
          onChange={(e, v) => v && setSelectedItem(v)}
          sx={{ width: 280 }}
          renderInput={(params) => <TextField {...params} label="Search item..." size="small" />}
        />
        <ToggleButtonGroup
          value={granularity}
          exclusive
          onChange={(e, v) => v && setGranularity(v)}
          size="small"
          sx={{
            '& .MuiToggleButton-root': {
              textTransform: 'none',
              px: 3,
              '&.Mui-selected': { bgcolor: 'white', fontWeight: 600, boxShadow: 1 },
            },
          }}
        >
          <ToggleButton value="Daily">Daily</ToggleButton>
          <ToggleButton value="Weekly">Weekly</ToggleButton>
          <ToggleButton value="Monthly">Monthly</ToggleButton>
        </ToggleButtonGroup>
        <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
          Last trained: <strong>{mockForecast.lastTrained}</strong>
        </Typography>
      </Box>

      {/* KPI Cards - Full Width Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            lg: 'repeat(4, 1fr)'
          },
          gap: 3,
          mb: 4
        }}
      >
        <Card sx={{ boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #f3f4f6', height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Recommended Order</Typography>
                <Typography variant="h4" fontWeight={800} color="#1B5E20" sx={{ mt: 1 }}>{mockForecast.recommendedOrder}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>for next {granularity.toLowerCase()} period</Typography>
              </Box>
              <Avatar sx={{ bgcolor: alpha('#1B5E20', 0.1), color: '#1B5E20', borderRadius: 2 }}>
                <InventoryIcon />
              </Avatar>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #f3f4f6', height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Model Confidence</Typography>
                <Typography variant="h4" fontWeight={800} color="#111827" sx={{ mt: 1 }}>{mockForecast.modelConfidence}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>based on historical fit</Typography>
              </Box>
              <Avatar sx={{ bgcolor: alpha('#1B5E20', 0.1), color: '#1B5E20', borderRadius: 2 }}>
                <VerifiedIcon />
              </Avatar>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #f3f4f6', height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Avg Daily Demand</Typography>
                <Typography variant="h4" fontWeight={800} sx={{ color: '#FF8F00', mt: 1 }}>{mockForecast.avgDailyDemand}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>peak on {mockForecast.peakDay}</Typography>
              </Box>
              <Avatar sx={{ bgcolor: alpha('#FF8F00', 0.1), color: '#FF8F00', borderRadius: 2 }}>
                <TrendingUpIcon />
              </Avatar>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #f3f4f6', height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Forecast Period</Typography>
                <Typography variant="h4" fontWeight={800} color="#111827" sx={{ mt: 1 }}>{granularity}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>selected granularity</Typography>
              </Box>
              <Avatar sx={{ bgcolor: alpha('#1B5E20', 0.1), color: '#1B5E20', borderRadius: 2 }}>
                <CalendarTodayIcon />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {/* Chart */}
      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Box>
              <Typography variant="h6" fontWeight={700}>{selectedItem?.name} — Predicted vs. Actual</Typography>
              <Typography variant="caption" color="text.secondary">
                Solid line = actual sales · Dashed line = AI prediction · Grey area = future forecast
              </Typography>
            </Box>
            <Chip label="Produce" size="small" variant="outlined" />
          </Stack>
          <DemandChart data={mockForecast.chartData} />
        </CardContent>
      </Card>
    </PageWrapper>
  );
}
