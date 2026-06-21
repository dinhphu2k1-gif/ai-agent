import LinearProgress from '@mui/material/LinearProgress'
import { styled } from '@mui/material/styles'
import React from 'react'
// material-ui

// loader style
const LoaderWrapper = styled('div')(({ theme }) => ({
  position: 'fixed',
  top: 0,
  left: 0,
  zIndex: 2001,
  width: '100%',
  '& > * + *': {
    marginTop: theme.spacing(2),
  },
}))

// ==============================|| Loader ||============================== //

const Loader: React.FC = () => (
  <LoaderWrapper>
    <LinearProgress color="primary" />
  </LoaderWrapper>
)

export default Loader
