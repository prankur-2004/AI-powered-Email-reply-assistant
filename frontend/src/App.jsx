import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/auth'

// ==================================================
// AXIOS INSTANCE
// ==================================================

const api = axios.create({
  baseURL: API_URL,
})

// ==================================================
// AUTOMATIC JWT TOKEN REFRESH
// ==================================================

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token)
    }
  })

  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status !== 401 ||
      originalRequest?._retry
    ) {
      return Promise.reject(error)
    }

    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.reload()

      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve,
          reject,
        })
      })
        .then((token) => {
          originalRequest.headers.Authorization =
            `Bearer ${token}`

          return api(originalRequest)
        })
        .catch((refreshError) => {
          return Promise.reject(refreshError)
        })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const response = await axios.post(
        `${API_URL}/token/refresh/`,
        {
          refresh: refreshToken,
        }
      )

      const newAccessToken = response.data.access

      localStorage.setItem(
        'access_token',
        newAccessToken
      )

      api.defaults.headers.common.Authorization =
        `Bearer ${newAccessToken}`

      processQueue(null, newAccessToken)

      originalRequest.headers.Authorization =
        `Bearer ${newAccessToken}`

      return api(originalRequest)
    } catch (refreshError) {
      processQueue(refreshError, null)

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')

      window.location.reload()

      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

// ==================================================
// APP
// ==================================================

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [checkingAuth, setCheckingAuth] = useState(true)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const [isRegistering, setIsRegistering] = useState(false)
  const [regUsername, setRegUsername] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regConfirmPassword, setRegConfirmPassword] = useState('')

  const [emails, setEmails] = useState([])
  const [selectedEmail, setSelectedEmail] = useState(null)

  const [analysis, setAnalysis] = useState(null)
  const [reply, setReply] = useState('')
  const [replyId, setReplyId] = useState(null)

  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const [accepted, setAccepted] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editedReply, setEditedReply] = useState('')

  const [feedbackRating, setFeedbackRating] = useState(null)
  const [feedbackHelpful, setFeedbackHelpful] = useState(null)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  // ==================================================
  // ADD EMAIL STATE
  // ==================================================

  const [showAddEmail, setShowAddEmail] = useState(false)

  // ==================================================
  // CONNECT EMAIL ACCOUNT STATE
  // ==================================================
  const [connectedAccounts, setConnectedAccounts] = useState([])
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [isSyncingEmails, setIsSyncingEmails] = useState(false)
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [connectTestSuccess, setConnectTestSuccess] = useState('')
  const [connectTestError, setConnectTestError] = useState('')
  const [connectForm, setConnectForm] = useState({
    provider: 'gmail',
    email_address: '',
    password: '',
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    use_ssl: true,
    max_emails: 15,
    auto_analyze: true,
  })

  const PROVIDER_DEFAULTS = {
    gmail: { host: 'imap.gmail.com', port: 993, ssl: true },
    outlook: { host: 'outlook.office365.com', port: 993, ssl: true },
    yahoo: { host: 'imap.mail.yahoo.com', port: 993, ssl: true },
    icloud: { host: 'imap.mail.me.com', port: 993, ssl: true },
    custom: { host: '', port: 993, ssl: true },
  }

  const [newEmail, setNewEmail] = useState({
    sender: '',
    recipient: '',
    subject: '',
    conversation_id: '',
    body: '',
    is_read: false,
  })

  // ==================================================
  // CHECK SAVED LOGIN
  // ==================================================

  useEffect(() => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      setCheckingAuth(false)
      return
    }

    api
      .get('/profile/')
      .then(() => {
        setIsLoggedIn(true)
        fetchEmails()
        fetchConnectedAccounts()
      })
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setIsLoggedIn(false)
      })
      .finally(() => {
        setCheckingAuth(false)
      })
  }, [])

  // ==================================================
  // FETCH EMAILS
  // ==================================================

  const fetchEmails = async () => {
    try {
      const response = await api.get('/emails/')
      setEmails(response.data)
    } catch (error) {
      console.error('Error fetching emails:', error)

      if (error.response?.status !== 401) {
        setMessage(
          error.response?.data?.detail ||
            error.response?.data?.message ||
            'Failed to fetch emails.'
        )
      }
    }
  }

  // ==================================================
  // LOGIN
  // ==================================================

  const handleLogin = async (event) => {
    event.preventDefault()

    setMessage('')
    setLoading(true)

    try {
      const response = await axios.post(
        `${API_URL}/login/`,
        {
          username,
          password,
        }
      )

      localStorage.setItem(
        'access_token',
        response.data.access
      )

      localStorage.setItem(
        'refresh_token',
        response.data.refresh
      )

      setIsLoggedIn(true)
      setMessage('Login successful!')

      await fetchEmails()
      await fetchConnectedAccounts()
    } catch (error) {
      console.error('Login error:', error)

      setMessage(
        error.response?.data?.detail ||
          error.response?.data?.message ||
          'Login failed. Please check your username and password.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // REGISTER
  // ==================================================

  const handleRegister = async (event) => {
    event.preventDefault()

    setMessage('')

    if (regPassword.length < 8) {
      setMessage('Password must be at least 8 characters long.')
      return
    }

    if (regPassword !== regConfirmPassword) {
      setMessage('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await axios.post(
        `${API_URL}/register/`,
        {
          username: regUsername,
          email: regEmail,
          password: regPassword,
        }
      )

      setMessage('Account created successfully! Please sign in.')
      setUsername(regUsername)
      setPassword(regPassword)
      setIsRegistering(false)
      setRegUsername('')
      setRegEmail('')
      setRegPassword('')
      setRegConfirmPassword('')
    } catch (error) {
      console.error('Registration error:', error)

      let errorMsg = 'Registration failed. Please check your input.'
      if (error.response?.data) {
        const data = error.response.data
        if (typeof data === 'string') {
          errorMsg = data
        } else if (data.detail) {
          errorMsg = data.detail
        } else if (data.message) {
          errorMsg = data.message
        } else {
          const errors = Object.entries(data)
            .map(([field, msgs]) => {
              const str = Array.isArray(msgs) ? msgs.join(' ') : msgs
              return `${field}: ${str}`
            })
            .join(' | ')
          if (errors) errorMsg = errors
        }
      }
      setMessage(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // LOGOUT
  // ==================================================

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    setIsLoggedIn(false)
    setConnectedAccounts([])
    setEmails([])
    setSelectedEmail(null)
    setAnalysis(null)
    setReply('')
    setReplyId(null)
    setAccepted(false)
    setEditing(false)
    setEditedReply('')

    setFeedbackRating(null)
    setFeedbackHelpful(null)
    setFeedbackComment('')
    setFeedbackSubmitted(false)

    setUsername('')
    setPassword('')
    setMessage('')
  }

  // ==================================================
  // EMAIL ACCOUNT INTEGRATION
  // ==================================================

  const fetchConnectedAccounts = async () => {
    try {
      const response = await api.get('/email-accounts/')
      setConnectedAccounts(response.data.accounts || [])
    } catch (err) {
      console.error('Error fetching email accounts:', err)
    }
  }

  const handleProviderChange = (provider) => {
    const defaults = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.custom
    setConnectForm((prev) => ({
      ...prev,
      provider,
      imap_host: defaults.host,
      imap_port: defaults.port,
      use_ssl: defaults.ssl,
    }))
    setConnectTestSuccess('')
    setConnectTestError('')
  }

  const handleTestConnection = async () => {
    setConnectTestSuccess('')
    setConnectTestError('')
    setIsTestingConnection(true)
    try {
      const res = await api.post('/email-accounts/test/', connectForm)
      setConnectTestSuccess(res.data.message || 'Connection verified successfully!')
    } catch (err) {
      setConnectTestError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          'Connection test failed. Please verify your credentials.'
      )
    } finally {
      setIsTestingConnection(false)
    }
  }

  const handleConnectEmailAccount = async (event) => {
    event.preventDefault()
    setConnectTestSuccess('')
    setConnectTestError('')
    setLoading(true)

    try {
      const res = await api.post('/email-accounts/', connectForm)
      setMessage(res.data.message || 'Email account connected successfully!')
      setShowConnectModal(false)
      setConnectForm({
        provider: 'gmail',
        email_address: '',
        password: '',
        imap_host: 'imap.gmail.com',
        imap_port: 993,
        use_ssl: true,
        max_emails: 15,
        auto_analyze: true,
      })
      await fetchConnectedAccounts()
      await fetchEmails()

      const synced = res.data.sync_result?.synced_count || 0
      if (synced > 0) {
        setMessage(`Connected successfully! Synced ${synced} recent email(s) with AI analysis.`)
      }
    } catch (err) {
      setConnectTestError(
        err.response?.data?.error ||
          err.response?.data?.message ||
          'Failed to connect email account. Please check credentials.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleSyncEmails = async (accountId = null) => {
    setIsSyncingEmails(true)
    setMessage('')
    try {
      const endpoint = accountId
        ? `/email-accounts/${accountId}/sync/`
        : '/email-accounts/sync/'
      const res = await api.post(endpoint, {
        max_emails: 15,
        auto_analyze: true,
      })
      await fetchEmails()
      await fetchConnectedAccounts()
      setMessage(
        res.data.message ||
          `Synced ${res.data.total_synced || 0} new email(s) with AI analysis!`
      )
    } catch (err) {
      console.error('Sync error:', err)
      setMessage(
        err.response?.data?.error ||
          err.response?.data?.message ||
          'Failed to sync emails from connected account.'
      )
    } finally {
      setIsSyncingEmails(false)
    }
  }

  const handleDisconnectAccount = async (accountId) => {
    if (!window.confirm('Are you sure you want to disconnect this email account?')) return
    setLoading(true)
    try {
      await api.delete(`/email-accounts/${accountId}/`)
      await fetchConnectedAccounts()
      setMessage('Email account disconnected successfully.')
    } catch (err) {
      console.error('Disconnect error:', err)
      setMessage('Failed to disconnect email account.')
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // SELECT EMAIL
  // ==================================================

  const handleSelectEmail = (email) => {
    setSelectedEmail(email)

    if (email.analysis) {
      setAnalysis(email.analysis)
    } else {
      setAnalysis(null)
    }
    setReply('')
    setReplyId(null)

    setAccepted(false)
    setEditing(false)
    setEditedReply('')

    setFeedbackRating(null)
    setFeedbackHelpful(null)
    setFeedbackComment('')
    setFeedbackSubmitted(false)

    setMessage('')
  }

  // ==================================================
  // ADD EMAIL
  // ==================================================

  const handleAddEmail = async (event) => {
    event.preventDefault()

    setLoading(true)
    setMessage('')

    try {
      const response = await api.post(
        '/emails/',
        newEmail
      )

      const createdEmail = response.data

      setEmails((previousEmails) => [
        createdEmail,
        ...previousEmails,
      ])

      setSelectedEmail(createdEmail)

      setAnalysis(null)
      setReply('')
      setReplyId(null)
      setAccepted(false)
      setEditing(false)
      setEditedReply('')

      setFeedbackRating(null)
      setFeedbackHelpful(null)
      setFeedbackComment('')
      setFeedbackSubmitted(false)

      setNewEmail({
        sender: '',
        recipient: '',
        subject: '',
        conversation_id: '',
        body: '',
        is_read: false,
      })

      setShowAddEmail(false)

      setMessage('Email added successfully!')
    } catch (error) {
      console.error('Add email error:', error)

      setMessage(
        error.response?.data?.detail ||
          error.response?.data?.message ||
          'Failed to add email.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // ANALYZE EMAIL
  // ==================================================

  const handleAnalyzeEmail = async () => {
    if (!selectedEmail) return

    setLoading(true)
    setMessage('')
    setAnalysis(null)

    try {
      const response = await api.post(
        `/emails/${selectedEmail.id}/analyze/`,
        {}
      )

      const analysisData =
        response.data.analysis ||
        response.data

      setAnalysis(analysisData)

      setMessage(
        'Email analyzed successfully!'
      )
    } catch (error) {
      console.error('Analysis error:', error)

      setMessage(
        error.response?.data?.detail ||
          error.response?.data?.message ||
          'Failed to analyze email.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // GENERATE AI REPLY
  // ==================================================

  const handleGenerateReply = async () => {
    if (!selectedEmail) return

    setLoading(true)
    setMessage('')
    setReply('')
    setReplyId(null)
    setAccepted(false)
    setEditing(false)

    setFeedbackRating(null)
    setFeedbackHelpful(null)
    setFeedbackComment('')
    setFeedbackSubmitted(false)

    try {
      const response = await api.post(
        `/emails/${selectedEmail.id}/reply/`,
        {}
      )

      const generatedReply =
        response.data.generated_reply ||
        response.data.reply ||
        response.data.ai_reply?.generated_reply ||
        ''

      const generatedReplyId =
        response.data.id ||
        response.data.reply_id ||
        response.data.ai_reply_id ||
        response.data.ai_reply?.id ||
        null

      setReply(generatedReply)
      setEditedReply(generatedReply)
      setReplyId(generatedReplyId)

      setMessage(
        'AI reply generated successfully!'
      )
    } catch (error) {
      console.error(
        'Reply generation error:',
        error
      )

      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Failed to generate AI reply.'

      setMessage(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // ACCEPT REPLY
  // ==================================================

  const handleAcceptReply = async () => {
    if (!replyId) {
      setMessage('Reply ID is missing.')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      await api.patch(
        `/replies/${replyId}/accept/`,
        {}
      )

      setAccepted(true)

      setMessage(
        'Reply accepted successfully!'
      )
    } catch (error) {
      console.error(
        'Accept error:',
        error
      )

      setMessage(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to accept reply.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // START EDITING
  // ==================================================

  const handleStartEditing = () => {
    setEditedReply(reply)
    setEditing(true)
  }

  // ==================================================
  // SAVE EDIT
  // ==================================================

  const handleSaveEdit = async () => {
    if (!replyId) {
      setMessage('Reply ID is missing.')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      const response = await api.patch(
        `/replies/${replyId}/edit/`,
        {
          generated_reply: editedReply,
        }
      )

      const updatedReply =
        response.data.generated_reply ||
        response.data.reply ||
        editedReply

      setReply(updatedReply)
      setEditedReply(updatedReply)
      setEditing(false)

      setMessage(
        'Reply edited successfully!'
      )
    } catch (error) {
      console.error(
        'Edit error:',
        error
      )

      setMessage(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to edit reply.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // REGENERATE REPLY
  // ==================================================

  const handleRegenerateReply = async () => {
    if (!replyId) {
      setMessage('Reply ID is missing.')
      return
    }

    setLoading(true)
    setMessage('')

    try {
      const response = await api.post(
        `/replies/${replyId}/regenerate/`,
        {}
      )

      const regeneratedReply =
        response.data.generated_reply ||
        response.data.reply ||
        response.data.ai_reply?.generated_reply ||
        ''

      const regeneratedReplyId =
        response.data.id ||
        response.data.reply_id ||
        response.data.ai_reply_id ||
        response.data.ai_reply?.id ||
        replyId

      setReply(regeneratedReply)
      setEditedReply(regeneratedReply)
      setReplyId(regeneratedReplyId)

      setAccepted(false)
      setEditing(false)

      setFeedbackRating(null)
      setFeedbackHelpful(null)
      setFeedbackComment('')
      setFeedbackSubmitted(false)

      setMessage(
        'Reply regenerated successfully!'
      )
    } catch (error) {
      console.error(
        'Regenerate error:',
        error
      )

      setMessage(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to regenerate reply.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // SUBMIT FEEDBACK
  // ==================================================

  const handleSubmitFeedback = async () => {
    if (!replyId) {
      setMessage('Reply ID is missing.')
      return
    }

    if (
      !feedbackRating &&
      feedbackHelpful === null
    ) {
      setMessage(
        'Please provide a rating or helpfulness feedback.'
      )
      return
    }

    setLoading(true)
    setMessage('')

    try {
      await api.post(
        `/replies/${replyId}/feedback/`,
        {
          rating: feedbackRating,
          is_helpful: feedbackHelpful,
          comment: feedbackComment,
        }
      )

      setFeedbackSubmitted(true)

      setMessage(
        'Feedback submitted successfully!'
      )
    } catch (error) {
      console.error(
        'Feedback error:',
        error
      )

      setMessage(
        error.response?.data?.message ||
          error.response?.data?.detail ||
          'Failed to submit feedback.'
      )
    } finally {
      setLoading(false)
    }
  }

  // ==================================================
  // CHECKING AUTH
  // ==================================================

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center relative overflow-hidden">

        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl" />

        <div className="relative text-center">
          <div className="w-14 h-14 mx-auto border-4 border-slate-700 border-t-indigo-500 rounded-full animate-spin" />

          <p className="text-slate-400 mt-5 text-sm">
            Checking authentication...
          </p>
        </div>

      </div>
    )
  }

  // ==================================================
  // LOGIN PAGE
  // ==================================================

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-4 relative overflow-hidden">

        {/* BACKGROUND EFFECTS */}

        <div className="absolute -top-52 -left-52 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-3xl" />

        <div className="absolute -bottom-52 -right-52 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-3xl" />

        <div className="absolute top-1/3 right-1/4 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl" />

        {/* LOGIN CARD */}

        <div className="relative w-full max-w-md">

          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl shadow-2xl shadow-black/40 p-8 backdrop-blur-xl">

            {/* LOGO */}

            <div className="text-center">

              <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-cyan-500 flex items-center justify-center text-4xl shadow-xl shadow-indigo-500/20">
                🤖
              </div>

              <div className="mt-6">

                <h1 className="text-3xl font-bold tracking-tight">
                  AI Email Assistant
                </h1>

                <p className="text-slate-400 mt-2 text-sm">
                  Intelligent email replies powered by AI
                </p>

              </div>

            </div>

            {/* AUTH TAB TOGGLE */}
            <div className="flex border-b border-slate-800/80 mt-6 mb-2">
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(false)
                  setMessage('')
                }}
                className={`flex-1 pb-3 text-sm font-semibold transition-all relative cursor-pointer ${
                  !isRegistering
                    ? 'text-indigo-400 border-b-2 border-indigo-500'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(true)
                  setMessage('')
                }}
                className={`flex-1 pb-3 text-sm font-semibold transition-all relative cursor-pointer ${
                  isRegistering
                    ? 'text-indigo-400 border-b-2 border-indigo-500'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Create Account
              </button>
            </div>

            {!isRegistering ? (
              /* LOGIN FORM */
              <form onSubmit={handleLogin} className="mt-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      👤
                    </span>
                    <input
                      type="text"
                      value={username}
                      onChange={(event) => setUsername(event.target.value)}
                      placeholder="Enter username"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <div className="mt-5">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      🔒
                    </span>
                    <input
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter password"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-7 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:from-indigo-500 hover:via-purple-500 hover:to-cyan-500 text-white font-semibold py-3.5 rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {loading ? 'Signing in...' : 'Sign In →'}
                </button>

                <p className="mt-5 text-center text-xs text-slate-400">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegistering(true)
                      setMessage('')
                    }}
                    className="text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-4 transition cursor-pointer"
                  >
                    Create a new account
                  </button>
                </p>
              </form>
            ) : (
              /* REGISTER FORM */
              <form onSubmit={handleRegister} className="mt-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Username
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      👤
                    </span>
                    <input
                      type="text"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      placeholder="Choose a username"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      ✉️
                    </span>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      🔒
                    </span>
                    <input
                      type="password"
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="At least 8 characters"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                      🛡️
                    </span>
                    <input
                      type="password"
                      value={regConfirmPassword}
                      onChange={(e) => setRegConfirmPassword(e.target.value)}
                      placeholder="Confirm password"
                      className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-600 rounded-xl pl-11 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-6 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:from-indigo-500 hover:via-purple-500 hover:to-cyan-500 text-white font-semibold py-3.5 rounded-xl transition-all duration-200 shadow-lg shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                >
                  {loading ? 'Creating Account...' : 'Create Account ✨'}
                </button>

                <p className="mt-5 text-center text-xs text-slate-400">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegistering(false)
                      setMessage('')
                    }}
                    className="text-indigo-400 hover:text-indigo-300 font-semibold underline underline-offset-4 transition cursor-pointer"
                  >
                    Sign in here
                  </button>
                </p>
              </form>
            )}

            {message && (
              <div className="mt-5 bg-slate-950/60 border border-slate-800 rounded-xl px-4 py-3">
                <p className="text-center text-sm text-slate-300">
                  {message}
                </p>
              </div>
            )}

            <div className="mt-7 pt-6 border-t border-slate-800 text-center">

              <p className="text-xs text-slate-600">
                AI-Powered Email Reply Assistant
              </p>

              <p className="text-[11px] text-slate-700 mt-1">
                Secure • Intelligent • Personalized
              </p>

            </div>

          </div>

        </div>

      </div>
    )
  }

  // ==================================================
  // DASHBOARD
  // ==================================================

  return (
    <div className="min-h-screen bg-slate-950 text-white relative overflow-x-hidden">

      {/* BACKGROUND GLOW */}

      <div className="fixed -top-60 -left-60 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="fixed -bottom-60 -right-60 w-[600px] h-[600px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* ==================================================
          HEADER
      ================================================== */}

      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">

        <div className="max-w-[1600px] mx-auto px-4 md:px-8 py-4 flex items-center justify-between">

          <div className="flex items-center gap-3">

            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-cyan-500 flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
              🤖
            </div>

            <div>

              <h1 className="text-lg md:text-xl font-bold tracking-tight">
                AI Email Assistant
              </h1>

              <div className="flex items-center gap-2 mt-0.5">

                <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />

                <p className="text-xs text-slate-500">
                  AI Workspace
                </p>

              </div>

            </div>

          </div>

          <div className="flex items-center gap-3">

            {/* SYNC & CONNECT BUTTONS */}
            <div className="flex items-center gap-2">
              {connectedAccounts.length > 0 && (
                <button
                  type="button"
                  onClick={() => handleSyncEmails()}
                  disabled={isSyncingEmails}
                  className="flex items-center gap-2 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 px-3.5 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
                  title="Fetch and analyze latest emails"
                >
                  <span className={isSyncingEmails ? 'inline-block animate-spin' : ''}>🔄</span>
                  <span className="hidden sm:inline">{isSyncingEmails ? 'Syncing...' : 'Sync Inbox'}</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => {
                  setConnectTestSuccess('')
                  setConnectTestError('')
                  setShowConnectModal(true)
                }}
                className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold transition shadow-lg shadow-emerald-600/20 cursor-pointer"
              >
                <span>⚡</span>
                <span>{connectedAccounts.length > 0 ? `${connectedAccounts.length} Connected` : 'Connect Email'}</span>
              </button>
            </div>

            <div className="hidden sm:block text-right">

              <p className="text-sm text-slate-300">
                Welcome back
              </p>

              <p className="text-xs text-slate-600">
                Your intelligent inbox
              </p>

            </div>

            <button
              onClick={handleLogout}
              className="border border-red-500/20 bg-red-500/5 hover:bg-red-500/10 hover:border-red-500/40 text-red-400 px-4 py-2.5 rounded-xl font-medium transition"
            >
              Logout
            </button>

          </div>

        </div>

      </header>

      {/* ==================================================
          MAIN
      ================================================== */}

      <main className="relative max-w-[1600px] mx-auto px-4 md:px-8 py-6">

        {/* MESSAGE */}

        {message && (
          <div className="mb-6 bg-indigo-500/5 border border-indigo-500/20 text-indigo-300 px-5 py-3.5 rounded-xl flex items-center gap-3 backdrop-blur-sm">

            <div className="w-7 h-7 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              ✓
            </div>

            <span className="text-sm">
              {message}
            </span>

          </div>
        )}

        {/* ==================================================
            DASHBOARD GRID
        ================================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-[350px_minmax(0,1fr)] gap-6">

          {/* ==================================================
              EMAIL SIDEBAR
          ================================================== */}

          <aside className="bg-slate-900/70 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl shadow-black/20 backdrop-blur-xl h-fit lg:sticky lg:top-24">

            {/* SIDEBAR HEADER */}

            <div className="p-5 border-b border-slate-800">

              <div className="flex items-center justify-between">

                <div>

                  <div className="flex items-center gap-2">

                    <h2 className="text-lg font-bold">
                      Inbox
                    </h2>

                    <span className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold px-2 py-1 rounded-full">
                      {emails.length}
                    </span>

                  </div>

                  <p className="text-xs text-slate-600 mt-1">
                    Your email workspace
                  </p>

                </div>

                <div className="flex items-center gap-1.5">
                  {connectedAccounts.length > 0 && (
                    <button
                      type="button"
                      onClick={() => handleSyncEmails()}
                      disabled={isSyncingEmails}
                      className="w-10 h-10 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-400 flex items-center justify-center text-sm transition"
                      title="Sync emails from connected account"
                    >
                      <span className={isSyncingEmails ? 'inline-block animate-spin' : ''}>🔄</span>
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setShowAddEmail(true)
                      setMessage('')
                    }}
                    className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xl transition shadow-lg shadow-indigo-600/20"
                    title="Add email manually"
                  >
                    +
                  </button>
                </div>

              </div>

              {/* CONNECTED ACCOUNT BADGE */}
              {connectedAccounts.length > 0 && (
                <div className="mt-4 p-2.5 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                      <p className="text-xs font-medium text-slate-300 truncate">
                        {connectedAccounts[0].email_address}
                      </p>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5 capitalize">
                      {connectedAccounts[0].provider} • {connectedAccounts[0].last_synced_at ? 'Synced' : 'Ready'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowConnectModal(true)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold ml-2 cursor-pointer"
                  >
                    Manage
                  </button>
                </div>
              )}

            </div>

            {/* EMAIL LIST */}

            <div className="p-3 max-h-[calc(100vh-180px)] overflow-y-auto">

              {emails.length === 0 ? (

                <div className="text-center py-10 px-4">

                  <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500/10 to-teal-500/10 border border-indigo-500/20 flex items-center justify-center text-3xl">
                    ⚡
                  </div>

                  <p className="text-slate-200 font-semibold text-sm mt-4">
                    No emails loaded
                  </p>

                  <p className="text-slate-500 text-xs mt-1 leading-relaxed">
                    Connect your email account to import and analyze real emails automatically.
                  </p>

                  <div className="mt-5 space-y-2">
                    <button
                      type="button"
                      onClick={() => setShowConnectModal(true)}
                      className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold py-2.5 px-3 rounded-xl transition shadow-lg shadow-emerald-600/20 cursor-pointer"
                    >
                      ⚡ Connect Email Account
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowAddEmail(true)}
                      className="text-xs text-slate-400 hover:text-slate-200 transition py-1 cursor-pointer"
                    >
                      Or enter email manually +
                    </button>
                  </div>

                </div>

              ) : (

                <div className="space-y-2">

                  {emails.map((email) => (

                    <button
                      key={email.id}
                      onClick={() =>
                        handleSelectEmail(email)
                      }
                      className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                        selectedEmail?.id === email.id
                          ? 'bg-indigo-500/10 border-indigo-500/40 shadow-lg shadow-indigo-500/5'
                          : 'border-transparent hover:bg-slate-800/60 hover:border-slate-700'
                      }`}
                    >

                      <div className="flex items-start gap-3">

                        <div
                          className={`w-10 h-10 shrink-0 rounded-xl flex items-center justify-center text-sm ${
                            selectedEmail?.id === email.id
                              ? 'bg-indigo-500/15 text-indigo-400'
                              : 'bg-slate-800 text-slate-500'
                          }`}
                        >
                          ✉
                        </div>

                        <div className="min-w-0 flex-1">

                          <div className="flex items-center justify-between gap-2">

                            <h3 className="font-semibold text-slate-200 truncate">
                              {email.subject ||
                                'No Subject'}
                            </h3>

                            <span className="text-[10px] text-slate-700 shrink-0">
                              #{email.id}
                            </span>

                          </div>

                          <p className="text-xs text-slate-500 mt-1 truncate">
                            {email.sender}
                          </p>

                          <p className="text-xs text-slate-600 mt-2 line-clamp-2 leading-relaxed">
                            {email.body}
                          </p>

                        </div>

                      </div>

                    </button>

                  ))}

                </div>

              )}

            </div>

          </aside>

          {/* ==================================================
              CONTENT
          ================================================== */}

          <section className="min-w-0">

            {!selectedEmail ? (

              /* EMPTY STATE */

              <div className="min-h-[650px] bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center justify-center backdrop-blur-xl shadow-2xl">

                <div className="text-center max-w-lg px-6">

                  <div className="relative w-24 h-24 mx-auto">

                    <div className="absolute inset-0 rounded-3xl bg-indigo-500/10 blur-xl" />

                    <div className="relative w-24 h-24 rounded-3xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-slate-700 flex items-center justify-center text-5xl">
                      📧
                    </div>

                  </div>

                  <h2 className="text-2xl md:text-3xl font-bold mt-7">
                    Select an email
                  </h2>

                  <p className="text-slate-500 mt-3 leading-relaxed">
                    Choose an email from your inbox to analyze
                    it and generate a personalized AI-powered
                    reply.
                  </p>

                  <button
                    onClick={() =>
                      setShowAddEmail(true)
                    }
                    className="mt-7 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:from-indigo-500 hover:via-purple-500 hover:to-cyan-500 px-6 py-3 rounded-xl font-semibold transition shadow-lg shadow-indigo-600/20"
                  >
                    + Add Email
                  </button>

                </div>

              </div>

            ) : (

              <div className="space-y-6">

                {/* ==================================================
                    EMAIL CARD
                ================================================== */}

                <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">

                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">

                    <div>

                      <div className="flex flex-wrap items-center gap-2 mb-3">

                        <span className="text-[11px] font-semibold tracking-wide bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-2.5 py-1 rounded-full">
                          EMAIL #{selectedEmail.id}
                        </span>

                        {selectedEmail.is_read && (
                          <span className="text-[11px] font-semibold tracking-wide bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-full">
                            ✓ Read
                          </span>
                        )}

                      </div>

                      <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                        {selectedEmail.subject ||
                          'No Subject'}
                      </h2>

                    </div>

                  </div>

                  {/* EMAIL META */}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-7">

                    <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">

                      <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                        From
                      </p>

                      <p className="text-sm text-slate-300 mt-2 break-all">
                        {selectedEmail.sender}
                      </p>

                    </div>

                    <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">

                      <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                        To
                      </p>

                      <p className="text-sm text-slate-300 mt-2 break-all">
                        {selectedEmail.recipient}
                      </p>

                    </div>

                  </div>

                  <div className="mt-4 bg-slate-950/60 rounded-xl p-4 border border-slate-800">

                    <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                      Conversation
                    </p>

                    <p className="text-sm text-slate-300 mt-2">
                      {selectedEmail.conversation_id ||
                        'N/A'}
                    </p>

                  </div>

                  {/* EMAIL BODY */}

                  <div className="mt-6 pt-6 border-t border-slate-800">

                    <p className="text-slate-300 whitespace-pre-wrap leading-8">
                      {selectedEmail.body}
                    </p>

                  </div>

                  {/* ACTIONS */}

                  <div className="flex flex-wrap gap-3 mt-7">

                    <button
                      onClick={handleAnalyzeEmail}
                      disabled={loading}
                      className="bg-purple-600/90 hover:bg-purple-500 text-white px-5 py-3 rounded-xl font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-purple-600/10"
                    >
                      {loading
                        ? 'Analyzing...'
                        : '🔍 Analyze Email'}
                    </button>

                    <button
                      onClick={handleGenerateReply}
                      disabled={loading}
                      className="bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white px-5 py-3 rounded-xl font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20"
                    >
                      🤖 Generate AI Reply
                    </button>

                  </div>

                </div>

                {/* ==================================================
                    ANALYSIS
                ================================================== */}

                {analysis && (

                  <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">

                    <div className="flex items-center gap-3 mb-6">

                      <div className="w-11 h-11 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
                        📊
                      </div>

                      <div>

                        <h2 className="text-xl font-bold">
                          Email Analysis
                        </h2>

                        <p className="text-xs text-slate-600 mt-0.5">
                          AI-powered email understanding
                        </p>

                      </div>

                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

                      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">

                        <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                          Intent
                        </p>

                        <p className="font-semibold mt-2 text-indigo-400 capitalize">
                          {analysis.intent || 'N/A'}
                        </p>

                      </div>

                      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">

                        <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                          Sentiment
                        </p>

                        <p className="font-semibold mt-2 text-emerald-400 capitalize">
                          {analysis.sentiment || 'N/A'}
                        </p>

                      </div>

                      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">

                        <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                          Urgency
                        </p>

                        <p className="font-semibold mt-2 text-orange-400 capitalize">
                          {analysis.urgency || 'N/A'}
                        </p>

                      </div>

                      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">

                        <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                          Topic
                        </p>

                        <p className="font-semibold mt-2 text-purple-400 capitalize">
                          {analysis.topic || 'N/A'}
                        </p>

                      </div>

                    </div>

                    {analysis.summary && (

                      <div className="mt-5 bg-slate-950/60 border border-slate-800 rounded-xl p-5">

                        <p className="text-[10px] text-slate-600 uppercase tracking-[0.15em] font-semibold">
                          Summary
                        </p>

                        <p className="text-slate-300 mt-2 leading-relaxed">
                          {analysis.summary}
                        </p>

                      </div>

                    )}

                  </div>

                )}

                {/* ==================================================
                    AI REPLY
                ================================================== */}

                {reply && (

                  <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">

                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-6">

                      <div className="flex items-center gap-3">

                        <div className="w-11 h-11 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                          🤖
                        </div>

                        <div>

                          <h2 className="text-xl font-bold">
                            AI Generated Reply
                          </h2>

                          <p className="text-xs text-slate-600 mt-0.5">
                            Personalized response
                          </p>

                        </div>

                      </div>

                      {accepted && (

                        <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-3 py-2 rounded-full text-xs font-semibold">
                          ✓ Accepted
                        </span>

                      )}

                    </div>

                    {/* REPLY */}

                    {editing ? (

                      <textarea
                        value={editedReply}
                        onChange={(event) =>
                          setEditedReply(
                            event.target.value
                          )
                        }
                        rows="10"
                        className="w-full bg-slate-950/70 border border-indigo-500/40 text-slate-200 rounded-xl p-5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-y leading-relaxed"
                      />

                    ) : (

                      <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-6 whitespace-pre-wrap text-slate-300 leading-8">
                        {reply}
                      </div>

                    )}

                    {/* REPLY ACTIONS */}

                    <div className="flex flex-wrap gap-3 mt-5">

                      {!editing && (
                        <>

                          <button
                            onClick={handleAcceptReply}
                            disabled={
                              loading || accepted
                            }
                            className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            ✓ Accept
                          </button>

                          <button
                            onClick={
                              handleStartEditing
                            }
                            disabled={loading}
                            className="bg-amber-600 hover:bg-amber-500 text-white px-5 py-2.5 rounded-xl font-semibold transition disabled:opacity-40"
                          >
                            ✏ Edit
                          </button>

                          <button
                            onClick={
                              handleRegenerateReply
                            }
                            disabled={loading}
                            className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl font-semibold transition disabled:opacity-40"
                          >
                            ↻ Regenerate
                          </button>

                        </>
                      )}

                      {editing && (
                        <>

                          <button
                            onClick={handleSaveEdit}
                            disabled={loading}
                            className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-semibold transition disabled:opacity-40"
                          >
                            Save Changes
                          </button>

                          <button
                            onClick={() => {
                              setEditing(false)
                              setEditedReply(reply)
                            }}
                            disabled={loading}
                            className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-5 py-2.5 rounded-xl font-semibold transition disabled:opacity-40"
                          >
                            Cancel
                          </button>

                        </>

                      )}

                    </div>




                  </div>

                )}

              </div>

            )}

          </section>

        </div>

      </main>

      {/* ==================================================
          CONNECT EMAIL ACCOUNT MODAL
      ================================================== */}

      {showConnectModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center px-4 z-50">
          <div className="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-black/60 p-6 max-h-[92vh] overflow-y-auto">
            
            {/* MODAL HEADER */}
            <div className="flex items-center justify-between pb-5 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl">
                  ⚡
                </div>
                <div>
                  <h2 className="text-xl font-bold">Connect Email Account</h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Sync and analyze emails directly from your real inbox
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowConnectModal(false)}
                className="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xl transition flex items-center justify-center cursor-pointer"
              >
                ×
              </button>
            </div>

            {/* EXISTING CONNECTED ACCOUNTS */}
            {connectedAccounts.length > 0 && (
              <div className="my-5 p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Currently Connected Accounts
                </p>
                <div className="space-y-2">
                  {connectedAccounts.map((acc) => (
                    <div
                      key={acc.id}
                      className="flex items-center justify-between p-3 bg-slate-900 border border-slate-800 rounded-lg"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-white truncate">
                            {acc.email_address}
                          </p>
                          <p className="text-xs text-slate-500 capitalize">
                            {acc.provider} ({acc.imap_host})
                            {acc.last_synced_at && ` • Synced ${new Date(acc.last_synced_at).toLocaleTimeString()}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleSyncEmails(acc.id)}
                          disabled={isSyncingEmails}
                          className="bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold px-3 py-1.5 rounded-lg border border-indigo-500/30 transition disabled:opacity-50 cursor-pointer"
                        >
                          {isSyncingEmails ? 'Syncing...' : '🔄 Sync'}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDisconnectAccount(acc.id)}
                          className="bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold px-3 py-1.5 rounded-lg border border-red-500/30 transition cursor-pointer"
                        >
                          Disconnect
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CONNECT FORM */}
            <form onSubmit={handleConnectEmailAccount} className="mt-5 space-y-4">
              
              {/* PROVIDER SELECTOR */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Select Provider
                </label>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                  {[
                    { id: 'gmail', label: 'Gmail', icon: '🔴' },
                    { id: 'outlook', label: 'Outlook', icon: '🔵' },
                    { id: 'yahoo', label: 'Yahoo', icon: '🟣' },
                    { id: 'icloud', label: 'iCloud', icon: '☁️' },
                    { id: 'custom', label: 'Custom', icon: '⚙️' },
                  ].map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handleProviderChange(p.id)}
                      className={`py-2.5 px-2 rounded-xl text-xs font-semibold border transition text-center flex flex-col items-center gap-1 cursor-pointer ${
                        connectForm.provider === p.id
                          ? 'bg-emerald-500/15 border-emerald-500 text-emerald-300 shadow-md shadow-emerald-500/10'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                      }`}
                    >
                      <span>{p.icon}</span>
                      <span>{p.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* HELPER GUIDE BOX */}
              <div className="bg-indigo-950/30 border border-indigo-500/20 rounded-xl p-3 text-xs leading-relaxed text-indigo-200">
                {connectForm.provider === 'gmail' && (
                  <div>
                    <span className="font-semibold text-indigo-300">Gmail Setup Guide:</span>
                    <ol className="list-decimal ml-4 mt-1 space-y-0.5 text-indigo-200/90">
                      <li>Enable 2-Step Verification on your Google Account.</li>
                      <li>Go to <strong>myaccount.google.com/apppasswords</strong>.</li>
                      <li>Generate a 16-character <strong>App Password</strong> (e.g. <code>xxxx xxxx xxxx xxxx</code>).</li>
                      <li>Paste that 16-character password below (not your regular account password).</li>
                    </ol>
                  </div>
                )}
                {connectForm.provider === 'outlook' && (
                  <div>
                    <span className="font-semibold text-indigo-300">Outlook / Office 365 Setup:</span>
                    <p className="mt-1 text-indigo-200/90">
                      Enter your full Microsoft email address and your password or Microsoft App Password.
                    </p>
                  </div>
                )}
                {connectForm.provider === 'yahoo' && (
                  <div>
                    <span className="font-semibold text-indigo-300">Yahoo Mail Setup:</span>
                    <p className="mt-1 text-indigo-200/90">
                      Go to Account Security &gt; Generate App Password, select 'Other App', and paste the password here.
                    </p>
                  </div>
                )}
                {connectForm.provider === 'icloud' && (
                  <div>
                    <span className="font-semibold text-indigo-300">iCloud Mail Setup:</span>
                    <p className="mt-1 text-indigo-200/90">
                      Create an app-specific password at appleid.apple.com under Sign-In and Security.
                    </p>
                  </div>
                )}
                {connectForm.provider === 'custom' && (
                  <div>
                    <span className="font-semibold text-indigo-300">Custom IMAP Server:</span>
                    <p className="mt-1 text-indigo-200/90">
                      Compatible with any IMAP email server (Hostinger, cPanel, Zoho, corporate domains).
                    </p>
                  </div>
                )}
              </div>

              {/* EMAIL ADDRESS */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={connectForm.email_address}
                  onChange={(e) => setConnectForm({ ...connectForm, email_address: e.target.value })}
                  placeholder={
                    connectForm.provider === 'gmail'
                      ? 'yourname@gmail.com'
                      : connectForm.provider === 'outlook'
                      ? 'yourname@outlook.com'
                      : 'email@yourdomain.com'
                  }
                  required
                  className="w-full bg-slate-950/80 border border-slate-700 text-white placeholder-slate-600 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition text-sm"
                />
              </div>

              {/* PASSWORD / APP PASSWORD */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  {connectForm.provider === 'gmail' ? '16-Character App Password' : 'Password / App Password'}
                </label>
                <input
                  type="password"
                  value={connectForm.password}
                  onChange={(e) => setConnectForm({ ...connectForm, password: e.target.value })}
                  placeholder={
                    connectForm.provider === 'gmail' ? 'abcd efgh ijkl mnop' : '••••••••••••••••'
                  }
                  required
                  className="w-full bg-slate-950/80 border border-slate-700 text-white placeholder-slate-600 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition text-sm"
                />
              </div>

              {/* CUSTOM IMAP HOST & PORT */}
              {connectForm.provider === 'custom' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      IMAP Host
                    </label>
                    <input
                      type="text"
                      value={connectForm.imap_host}
                      onChange={(e) => setConnectForm({ ...connectForm, imap_host: e.target.value })}
                      placeholder="mail.yourdomain.com"
                      required
                      className="w-full bg-slate-950/80 border border-slate-700 text-white placeholder-slate-600 rounded-xl px-4 py-2.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Port
                    </label>
                    <input
                      type="number"
                      value={connectForm.imap_port}
                      onChange={(e) => setConnectForm({ ...connectForm, imap_port: parseInt(e.target.value) || 993 })}
                      className="w-full bg-slate-950/80 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-sm"
                    />
                  </div>
                </div>
              )}

              {/* SYNC OPTIONS */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Emails to Fetch
                  </label>
                  <select
                    value={connectForm.max_emails}
                    onChange={(e) => setConnectForm({ ...connectForm, max_emails: parseInt(e.target.value) || 15 })}
                    className="w-full bg-slate-950/80 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-sm"
                  >
                    <option value={5}>Latest 5 emails</option>
                    <option value={10}>Latest 10 emails</option>
                    <option value={15}>Latest 15 emails</option>
                    <option value={25}>Latest 25 emails</option>
                    <option value={50}>Latest 50 emails</option>
                  </select>
                </div>

                <div className="flex items-center pt-5">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={connectForm.auto_analyze}
                      onChange={(e) => setConnectForm({ ...connectForm, auto_analyze: e.target.checked })}
                      className="w-4 h-4 rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-emerald-500"
                    />
                    <span>Auto-analyze with AI on import</span>
                  </label>
                </div>
              </div>

              {/* TEST SUCCESS OR ERROR MESSAGE */}
              {connectTestSuccess && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                  <span>✓</span>
                  <span>{connectTestSuccess}</span>
                </div>
              )}

              {connectTestError && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-xs flex items-start gap-2">
                  <span className="shrink-0 mt-0.5">⚠️</span>
                  <span>{connectTestError}</span>
                </div>
              )}

              {/* ACTION BUTTONS */}
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={isTestingConnection || !connectForm.email_address || !connectForm.password}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-5 py-2.5 rounded-xl text-xs font-semibold transition disabled:opacity-40 cursor-pointer"
                >
                  {isTestingConnection ? 'Testing Connection...' : '🔌 Test Connection'}
                </button>

                <button
                  type="submit"
                  disabled={loading || !connectForm.email_address || !connectForm.password}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white px-6 py-2.5 rounded-xl text-xs font-semibold transition shadow-lg shadow-emerald-600/20 disabled:opacity-40 cursor-pointer"
                >
                  {loading ? 'Connecting & Syncing...' : '⚡ Connect & Import Emails'}
                </button>
              </div>

            </form>

          </div>
        </div>
      )}

      {/* ==================================================
          ADD EMAIL MODAL
      ================================================== */}

      {showAddEmail && (

        <div className="fixed inset-0 bg-black/75 backdrop-blur-md flex items-center justify-center px-4 z-50">

          <div className="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl shadow-black/60 p-6 max-h-[90vh] overflow-y-auto">

            {/* MODAL HEADER */}

            <div className="flex items-center justify-between mb-7">

              <div>

                <div className="flex items-center gap-3">

                  <div className="w-11 h-11 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
                    ✉
                  </div>

                  <div>

                    <h2 className="text-2xl font-bold">
                      Add New Email
                    </h2>

                    <p className="text-xs text-slate-600 mt-1">
                      Add an email to test the AI assistant.
                    </p>

                  </div>

                </div>

              </div>

              <button
                onClick={() =>
                  setShowAddEmail(false)
                }
                className="w-9 h-9 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white text-xl transition"
              >
                ×
              </button>

            </div>

            {/* FORM */}

            <form onSubmit={handleAddEmail}>

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Sender Email
              </label>

              <input
                type="email"
                value={newEmail.sender}
                onChange={(event) =>
                  setNewEmail({
                    ...newEmail,
                    sender: event.target.value,
                  })
                }
                placeholder="sender@example.com"
                className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-700 rounded-xl px-4 py-3.5 mb-5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                required
              />

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Recipient Email
              </label>

              <input
                type="email"
                value={newEmail.recipient}
                onChange={(event) =>
                  setNewEmail({
                    ...newEmail,
                    recipient: event.target.value,
                  })
                }
                placeholder="recipient@example.com"
                className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-700 rounded-xl px-4 py-3.5 mb-5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                required
              />

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Subject
              </label>

              <input
                type="text"
                value={newEmail.subject}
                onChange={(event) =>
                  setNewEmail({
                    ...newEmail,
                    subject: event.target.value,
                  })
                }
                placeholder="Enter email subject"
                className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-700 rounded-xl px-4 py-3.5 mb-5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
                required
              />

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Conversation ID
              </label>

              <input
                type="text"
                value={newEmail.conversation_id}
                onChange={(event) =>
                  setNewEmail({
                    ...newEmail,
                    conversation_id:
                      event.target.value,
                  })
                }
                placeholder="conversation-002"
                className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-700 rounded-xl px-4 py-3.5 mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
              />

              <p className="text-xs text-slate-600 mb-5">
                Use the same Conversation ID for related emails.
              </p>

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Email Body
              </label>

              <textarea
                value={newEmail.body}
                onChange={(event) =>
                  setNewEmail({
                    ...newEmail,
                    body: event.target.value,
                  })
                }
                placeholder="Enter the email content..."
                rows="8"
                className="w-full bg-slate-950/70 border border-slate-700 text-white placeholder-slate-700 rounded-xl px-4 py-3.5 mb-6 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition resize-y"
                required
              />

              {/* MODAL BUTTONS */}

              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3">

                <button
                  type="button"
                  onClick={() => {
                    setShowAddEmail(false)

                    setNewEmail({
                      sender: '',
                      recipient: '',
                      subject: '',
                      conversation_id: '',
                      body: '',
                      is_read: false,
                    })
                  }}
                  disabled={loading}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-6 py-3 rounded-xl font-semibold transition disabled:opacity-40"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:from-indigo-500 hover:via-purple-500 hover:to-cyan-500 text-white px-6 py-3 rounded-xl font-semibold transition shadow-lg shadow-indigo-600/20 disabled:opacity-40"
                >
                  {loading
                    ? 'Saving...'
                    : 'Save Email →'}
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

    </div>
  )
}

export default App