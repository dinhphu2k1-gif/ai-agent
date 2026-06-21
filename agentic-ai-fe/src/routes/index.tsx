import MainRouter from './main-router'
import { createBrowserRouter, RouterProvider as RRDRouterProvider } from 'react-router-dom'

export default function RouterProvider(): React.ReactNode {
  const router = createBrowserRouter([MainRouter])

  return <RRDRouterProvider router={router} />
}
