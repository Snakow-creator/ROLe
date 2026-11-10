import { readdirSync } from 'node:fs'
import process from 'node:process'

const avatarDirectory = new URL('../public/avatars/', import.meta.url)
const avatarVariants = ['man', 'woman']
const expectedFiles = avatarVariants.map(variant => `default_avatar_${variant}.png`)

for (let rank = 1; rank <= 20; rank += 1) {
  for (const variant of avatarVariants) {
    expectedFiles.push(`standart_avatar${rank}_${variant}.png`)
  }
}

const entries = readdirSync(avatarDirectory, { withFileTypes: true })
const actualFiles = new Set(entries.filter(entry => entry.isFile()).map(entry => entry.name))
const missingFiles = expectedFiles.filter(file => !actualFiles.has(file))

if (missingFiles.length > 0) {
  console.error(`Отсутствуют файлы в frontend/public/avatars:\n${missingFiles.join('\n')}`)
  process.exitCode = 1
} else {
  console.log(`В frontend/public/avatars найдены все ${expectedFiles.length} аватара.`)
}
