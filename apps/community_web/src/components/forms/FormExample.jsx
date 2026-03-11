import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import MenuItem from '@mui/material/MenuItem';
import FormControlLabel from '@mui/material/FormControlLabel';

import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import EmailIcon from '@mui/icons-material/Email';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';

import {
  StyledTextField,
  StyledSelect,
  StyledSwitch,
  StyledCheckbox,
  StyledSlider,
  FormSection,
  IconTextField,
  ChipSelect,
  FormGroup,
  StyledRadioGroup,
} from './FormComponents';

// Example form showing all enhanced components
export default function FormExample() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: '',
    permissions: [],
    notifications: true,
    theme: 'light',
    volume: 50,
    agree: false,
  });

  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' 
      ? event.target.checked 
      : event.target.value;
    setFormData({ ...formData, [field]: value });
  };

  const handleSliderChange = (field) => (event, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    // Handle form submission
  };

  return (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      sx={{
        p: 4,
        borderRadius: 2,
        boxShadow: (theme) => theme.shadows[1],
      }}
    >
      <Typography variant="h5" gutterBottom>
        Account Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage your account preferences and security settings
      </Typography>
      
      <Divider sx={{ mb: 4 }} />

      <FormSection title="Basic Information" subtitle="Your account details">
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <StyledTextField
              fullWidth
              label="Username"
              value={formData.username}
              onChange={handleChange('username')}
              required
              helperText="Choose a unique username"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <IconTextField
              fullWidth
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleChange('email')}
              required
              icon={<EmailIcon />}
              helperText="We'll never share your email"
            />
          </Grid>
          
          <Grid item xs={12}>
            <IconTextField
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange('password')}
              required
              icon={showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
              iconPosition="end"
              onIconClick={() => setShowPassword(!showPassword)}
              helperText="Use at least 8 characters"
            />
          </Grid>
        </Grid>
      </FormSection>

      <FormSection title="Role & Permissions" subtitle="Configure access levels">
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <FormGroup label="Role" required>
              <StyledSelect
                value={formData.role}
                onChange={handleChange('role')}
                displayEmpty
              >
                <MenuItem value="">Select a role</MenuItem>
                <MenuItem value="admin">Administrator</MenuItem>
                <MenuItem value="editor">Editor</MenuItem>
                <MenuItem value="viewer">Viewer</MenuItem>
              </StyledSelect>
            </FormGroup>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormGroup label="Permissions">
              <ChipSelect
                value={formData.permissions}
                onChange={handleChange('permissions')}
                options={[
                  { value: 'read', label: 'Read' },
                  { value: 'write', label: 'Write' },
                  { value: 'delete', label: 'Delete' },
                  { value: 'share', label: 'Share' },
                ]}
              />
            </FormGroup>
          </Grid>
        </Grid>
      </FormSection>

      <FormSection title="Preferences" subtitle="Customize your experience">
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body2">
                Email Notifications
              </Typography>
              <StyledSwitch
                checked={formData.notifications}
                onChange={handleChange('notifications')}
              />
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <StyledRadioGroup
              label="Theme"
              value={formData.theme}
              onChange={handleChange('theme')}
              options={[
                { value: 'light', label: 'Light' },
                { value: 'dark', label: 'Dark' },
                { value: 'auto', label: 'Auto' },
              ]}
              row
            />
          </Grid>
          
          <Grid item xs={12}>
            <FormGroup label="Volume">
              <StyledSlider
                value={formData.volume}
                onChange={handleSliderChange('volume')}
                valueLabelDisplay="auto"
                marks={[
                  { value: 0, label: '0' },
                  { value: 50, label: '50' },
                  { value: 100, label: '100' },
                ]}
              />
            </FormGroup>
          </Grid>
        </Grid>
      </FormSection>

      <Divider sx={{ my: 3 }} />

      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <FormControlLabel
          control={
            <StyledCheckbox
              checked={formData.agree}
              onChange={handleChange('agree')}
            />
          }
          label="I agree to the terms and conditions"
        />
        
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<CancelIcon />}
            onClick={() => {/* Handle cancel */}}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            startIcon={<SaveIcon />}
            disabled={!formData.agree}
          >
            Save Changes
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}