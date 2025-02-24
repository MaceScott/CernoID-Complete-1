import { generateApi } from 'swagger-typescript-api'
import { resolve } from 'path'

export async function generateApiDocs() {
  await generateApi({
    name: 'api.docs.ts',
    output: resolve(process.cwd(), 'docs/api'),
    url: 'http://localhost:3000/api/openapi.json',
    generateClient: true,
    generateRouteTypes: true,
  })
} 