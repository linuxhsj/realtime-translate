command: "cat /tmp/translation_output.json 2>/dev/null || echo '{\"original\":\"等待音频输入...\",\"translated\":\"\",\"language\":\"\",\"timestamp\":\"\"}'"
refreshFrequency: 500

render: (output) ->
  try
    data = JSON.parse(output)
  catch
    data = {
      original: "等待音频输入...",
      translated: "",
      language: "",
      timestamp: ""
    }
  
  langIcon = @getLangIcon(data.language)
  hasTranslation = data.translated and data.translated != data.original
  
  """
  <div class="translation-widget">
    <div class="header">
      <span class="timestamp">#{data.timestamp}</span>
      <span class="language">#{langIcon} #{data.language.toUpperCase()}</span>
    </div>
    <div class="content">
      <div class="original-section">
        <span class="label">📝 原文</span>
        <div class="text original">#{data.original}</div>
      </div>
      #{if hasTranslation then """
      <div class="translated-section">
        <span class="label">🎯 译文</span>
        <div class="text translated">#{data.translated}</div>
      </div>
      """ else ""}
    </div>
  </div>
  """

getLangIcon: (lang) ->
  icons = {
    'en': '🇺🇸',
    'zh': '🇨🇳',
    'ja': '🇯🇵',
    'ko': '🇰🇷',
    'es': '🇪🇸',
    'fr': '🇫🇷',
    'de': '🇩🇪',
    'ru': '🇷🇺',
    'pt': '🇵🇹',
    'it': '🇮🇹'
  }
  return icons[lang] || '🌐'

style: """
  .translation-widget
    position: fixed
    bottom: 80px
    right: 20px
    max-width: 650px
    min-width: 300px
    background: rgba(0, 0, 0, 0.9)
    color: white
    padding: 0
    border-radius: 12px
    font-size: 15px
    line-height: 1.5
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif
    box-shadow: 0 8px 32px rgba(0,0,0,0.4)
    z-index: 10000
    backdrop-filter: blur(10px)
    border: 1px solid rgba(255,255,255,0.1)
    overflow: hidden
    
  .header
    display: flex
    justify-content: space-between
    align-items: center
    padding: 10px 15px
    background: rgba(255,255,255,0.05)
    border-bottom: 1px solid rgba(255,255,255,0.1)
    font-size: 12px
    color: rgba(255,255,255,0.7)
    
  .timestamp
    font-family: 'SF Mono', Monaco, monospace
    
  .language
    font-weight: 500
    
  .content
    padding: 15px
    
  .original-section, .translated-section
    margin-bottom: 10px
    
  .translated-section
    margin-top: 12px
    padding-top: 12px
    border-top: 1px solid rgba(255,255,255,0.1)
    
  .label
    display: inline-block
    font-size: 11px
    color: rgba(255,255,255,0.5)
    margin-bottom: 5px
    text-transform: uppercase
    letter-spacing: 0.5px
    
  .text
    white-space: pre-wrap
    word-wrap: break-word
    
  .original
    color: rgba(255,255,255,0.9)
    
  .translated
    color: #4FC3F7
    font-weight: 500
"""
