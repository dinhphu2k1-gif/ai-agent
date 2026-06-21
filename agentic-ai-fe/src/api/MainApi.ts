import { ApiService } from '.'

class MainApi extends ApiService {
  constructor() {
    super(import.meta.env.VITE_APP_API_URL)
  }
}

export default new MainApi()
