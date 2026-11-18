

export function saveTextFile(filename, content) {
  const native = window.JiGouNative
  if (native && typeof native.saveTextFile === 'function') {
    native.saveTextFile(filename, content)
    return 'native'
  }

  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  return 'browser'
}

export function saveImageFile(filename, dataUrl) {
  const native = window.JiGouNative
  if (native && typeof native.saveImage === 'function') {
    native.saveImage(filename, dataUrl)
    return 'native'
  }

  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  return 'browser'
}

export function savePdfFile(filename, blob) {
  const native = window.JiGouNative
  if (native && typeof native.savePdf === 'function') {
    
    const reader = new FileReader()
    reader.onload = () => native.savePdf(filename, reader.result)
    reader.readAsDataURL(blob)
    return 'native'
  }

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
  return 'browser'
}
