import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Typography } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TimelineIcon from '@mui/icons-material/Timeline';
import NotificationsIcon from '@mui/icons-material/Notifications';
import LocalOfferIcon from '@mui/icons-material/LocalOffer';
import SettingsIcon from '@mui/icons-material/Settings';
import { NAV_ITEMS } from '../../utils/constants';

const DRAWER_WIDTH = 250;
const iconMap = {
  Dashboard: <DashboardIcon />,
  Inventory: <Inventory2OutlinedIcon />,
  TrendingUp: <TrendingUpIcon />,
  Timeline: <TimelineIcon />,
  Notifications: <NotificationsIcon />,
  LocalOffer: <LocalOfferIcon />,
  Settings: <SettingsIcon />,
};

export default function Sidebar() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        display: { xs: 'none', md: 'block' },
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          borderRight: '1px solid #E0E0E0',
        }
      }}
      open
    >
      <Toolbar sx={{ borderBottom: '1px solid #E0E0E0' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ fontSize: 24 }}>🌿</Typography>
          <Typography
            variant="h6"
            sx={{
              color: '#1B5E20',
              fontWeight: 800,
              fontStyle: 'italic'
            }}
          >
            FreshFlow
          </Typography>
        </Box>
      </Toolbar>
      <List sx={{ px: 1, pt: 2 }}>
        {NAV_ITEMS.map((n) => {
          const active = pathname === n.path;
          return (
            <ListItemButton
              key={n.path}
              selected={active}
              onClick={() => navigate(n.path)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                background: active ? 'linear-gradient(90deg, #1B5E20 0%, #388E3C 100%)' : 'transparent',
                color: active ? 'white' : 'inherit',
                '&:hover': {
                  background: active ? 'linear-gradient(90deg, #1B5E20 0%, #388E3C 100%)' : 'rgba(27, 94, 32, 0.08)',
                },
                '&.Mui-selected': {
                  background: 'linear-gradient(90deg, #1B5E20 0%, #388E3C 100%)',
                  color: 'white',
                  '&:hover': {
                    background: 'linear-gradient(90deg, #1B5E20 0%, #388E3C 100%)',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: active ? 'white' : 'inherit'
                }}
              >
                {iconMap[n.icon]}
              </ListItemIcon>
              <ListItemText
                primary={n.label}
                primaryTypographyProps={{ fontWeight: active ? 600 : 400 }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Drawer>
  );
}

export { DRAWER_WIDTH };
