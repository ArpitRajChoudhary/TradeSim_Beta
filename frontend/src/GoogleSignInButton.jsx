
import { useEffect, useRef, useState } from 'react'

const GOOGLE_CLIENT_ID =
  '543028030896-aq2fv65t4c623s3tsoesebqf8k1mett1.apps.googleusercontent.com'

function GoogleSignInButton({ onSuccess }) {
  const buttonRef = useRef(null)
  const initializedRef = useRef(false)

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false

    function initializeGoogleSignIn() {
      if (
        cancelled ||
        !window.google?.accounts?.id ||
        !buttonRef.current
      ) {
        return
      }

      buttonRef.current.replaceChildren()

      // Initialize Google only once, even with React Strict Mode.
      if (!initializedRef.current) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,

          callback: async (response) => {
            if (!response.credential) {
              setError('Google did not return a valid credential.')
              return
            }

            setLoading(true)
            setError('')

            try {
              const result = await fetch('/api/auth/google', {
                method: 'POST',
                credentials: 'include',
                headers: {
                  'Content-Type': 'application/json',
                  Accept: 'application/json',
                },
                body: JSON.stringify({
                  credential: response.credential,
                }),
              })

              const data = await result.json()

              if (!result.ok) {
                throw new Error(
                  data.detail || 'Google sign-in failed.'
                )
              }

              onSuccess(data.user)
            } catch (err) {
              setError(err.message || 'Unable to sign in.')
            } finally {
              setLoading(false)
            }
          },
        })

        initializedRef.current = true
      }

      // Render the button even when initialization has already happened.
      window.google.accounts.id.renderButton(
        buttonRef.current,
        {
          type: 'standard',
          theme: 'filled_black',
          size: 'large',
          text: 'signin_with',
          shape: 'rectangular',
          width: 280,
        }
      )
    }

    const script = document.getElementById(
      'google-identity-script'
    )

    if (window.google?.accounts?.id) {
      initializeGoogleSignIn()
    } else if (script) {
      script.addEventListener(
        'load',
        initializeGoogleSignIn
      )
    } else {
      setError('Google sign-in could not be loaded.')
    }

    return () => {
      cancelled = true

      script?.removeEventListener(
        'load',
        initializeGoogleSignIn
      )
    }
  }, [onSuccess])

  return (
    <div className="google-signin-container">
      <div ref={buttonRef} />

      {loading && (
        <p className="google-signin-status">
          Signing you in...
        </p>
      )}

      {error && (
        <p className="google-signin-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}

export default GoogleSignInButton
