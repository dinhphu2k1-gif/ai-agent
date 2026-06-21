import { Provider } from 'react-redux'
import { store } from '@/redux'
import MessageToast from '@/components/MessageToast'
import ThemeProvider from '@/theme'
import RouterProvider from '@/routes'

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <RouterProvider />
        <MessageToast />
      </ThemeProvider>
    </Provider>
  )
}

export default App
