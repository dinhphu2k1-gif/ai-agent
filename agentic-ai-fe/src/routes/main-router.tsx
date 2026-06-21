import { lazy } from 'react'
import MainLayout from '@/layout/main-layout'
import type { RouteObject } from 'react-router-dom'

const TestPge = () => <div>abc</div>
const UserManagementPage = lazy(() => import('@/pages/user-management'))
const RoleManagementPage = lazy(() => import('@/pages/role-management'))
const GroupManagementPage = lazy(() => import('@/pages/group-management'))
const ChatPage = lazy(() => import('@/pages/chat'))

const MainRouter: RouteObject = {
  path: '/',
  errorElement: <div> 404 | not found</div>,
  hydrateFallbackElement: <div>loading</div>,
  element: <MainLayout />,
  children: [
    {
      path: 'chat',
      children: [
        {
          path: ':channelId',
          element: <ChatPage />,
        },
        {
          path: '',
          element: <ChatPage />,
        },
      ],
    },
    {
      path: 'admin',
      children: [
        {
          path: 'users',
          element: <UserManagementPage />,
        },
        {
          path: 'roles',
          element: <RoleManagementPage />,
        },
        {
          path: 'groups',
          element: <GroupManagementPage />,
        },
        {
          path: 'group-user',
          children: [
            {
              path: 'screen',
              element: <TestPge />,
            },
            {
              path: 'feature',
              element: <TestPge />,
            },
            {
              path: 'author',
              element: <TestPge />,
            },
          ],
        },
      ],
    },
    {
      path: 'early-warning',
      children: [
        {
          path: 'list',
          element: <TestPge />,
        },
      ],
    },
    {
      path: '*',
      element: <div>404 | not found</div>,
    },
  ],
}

export default MainRouter
