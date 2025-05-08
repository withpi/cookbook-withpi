// vercel-edge-function-webhook-example.ts
const WITHPI_API_URL: string = 'https://api.withpi.ai/v1/scoring_system/score';
const DEFAULT_QUESTION: string = 'Is this response helpful and accurate?';

interface HeliconeWebhookPayload {
  request_id: string; // Unique ID for the request
  created_at: string; // ISO timestamp
  model: string; // Model name (e.g., "gpt-4")
  prompt_tokens: number; // Number of tokens in prompt
  completion_tokens: number; // Number of tokens in completion
  total_tokens: number; // Total tokens used
  latency: number; // Request latency in ms
  status: string; // "success" or "error"
  feedback: any; // User feedback if available

  // The original API request body sent to the LLM provider
  request_body: {
    model: string;
    messages?: Array<{
      // For chat completions (OpenAI, Anthropic, etc.)
      role: string; // "system", "user", "assistant"
      content: string; // The actual message content
    }>;
    prompt?: string; // For completion APIs (older format)
    temperature?: number;
    max_tokens?: number;
    // ...other model-specific parameters
  };

  // The response received from the LLM provider
  response_body: {
    choices?: Array<{
      message?: {
        // For chat completions
        role: string;
        content: string;
      };
      text?: string; // For completion APIs
      finish_reason: string;
    }>;
    // ...other response fields
  };

  // Custom properties added during request
  properties: Record<string, string>;

  // User-provided metadata
  user_id?: string;
  user_properties?: Record<string, string>;
}
export const runtime = 'edge';

/**
 * Creates an HMAC signature using Web Crypto API (Edge compatible)
 */
async function createHmacSignature(secret: string, message: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyData = encoder.encode(secret);
  const messageData = encoder.encode(message);

  const key = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );

  const signature = await crypto.subtle.sign('HMAC', key, messageData);
  return Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Verifies the HMAC signature from Helicone using Web Crypto API
 */
async function verifyHeliconeHmac(
  headers: Headers,
  rawBody: string,
  webhookSecret: string,
): Promise<boolean> {
  try {
    // Get the signature from headers
    const signature = headers.get('helicone-signature');
    if (!signature) {
      console.warn('No Helicone signature provided');
      return false;
    }

    // Generate HMAC signature using Web Crypto API
    const calculatedSignature = await createHmacSignature(webhookSecret, rawBody);

    // Time-safe comparison to prevent timing attacks
    return timingSafeEqual(calculatedSignature, signature);
  } catch (error) {
    console.error('Error verifying HMAC:', error);
    return false;
  }
}

/**
 * Performs a time-safe comparison of two strings (Edge compatible)
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  const aBytes = new TextEncoder().encode(a);
  const bBytes = new TextEncoder().encode(b);

  for (let i = 0; i < aBytes.length; i++) {
    result |= aBytes[i] ^ bBytes[i];
  }

  return result === 0;
}

export async function POST(request: Request) {
  // Get the raw request body for HMAC verification
  const rawBody = await request.text();

  // Verify environment variables
  const withpiApiKey = process.env.WITHPI_API_KEY;
  if (!withpiApiKey) {
    throw new Error('WITHPI_API_KEY is not configured');
  }

  const heliconeApiKey = process.env.HELICONE_API_KEY;
  if (heliconeApiKey) {
    throw new Error('HELICONE_API_KEY is not configured');
  }

  const heliconeWebhookSecret = process.env.HELICONE_WEBHOOK_SECRET;
  if (!heliconeWebhookSecret) {
    throw new Error('HELICONE_WEBHOOK_SECRET is not configured');
  }

  // Verify HMAC signature
  const isAuthenticated = await verifyHeliconeHmac(request.headers, rawBody, heliconeWebhookSecret);
  if (!isAuthenticated) {
    return new Response(
      JSON.stringify({
        status: 'error',
        message: 'Invalid HMAC signature',
      }),
      {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      },
    );
  }

  const data = JSON.parse(rawBody) as HeliconeWebhookPayload;

  // Extract the input/prompt
  let input = '';
  if (data.request_body.messages && data.request_body.messages.length > 0) {
    // For chat completions, use the last user message
    const userMessages = data.request_body.messages.filter((m) => m.role === 'user');
    if (userMessages.length > 0) {
      input = userMessages[userMessages.length - 1].content;
    }
  } else if (data.request_body.prompt) {
    // For completion APIs
    input = data.request_body.prompt;
  }

  // Extract the response/completion
  let response = '';
  if (data.response_body.choices && data.response_body.choices.length > 0) {
    const firstChoice = data.response_body.choices[0];
    if (firstChoice.message && firstChoice.message.content) {
      // Chat completions format
      response = firstChoice.message.content;
    } else if (firstChoice.text) {
      // Completion API format
      response = firstChoice.text;
    }
  }

  // The payload as specified
  const scoring_payload = {
    scoring_spec: [
      {
        is_lower_score_desirable: false,
        question: DEFAULT_QUESTION,
      },
    ],
    llm_input: input,
    llm_output: response,
  };

  try {
    // Execute the scoring function
    // Send the POST request to the Helicone webhook
    const piApiResponse = await fetch(WITHPI_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': withpiApiKey,
      },
      body: JSON.stringify(scoring_payload),
    });

    if (!piApiResponse.ok) {
      throw new Error(`API request failed: ${piApiResponse.status} ${piApiResponse.statusText}`);
    }

    const pi_score = await piApiResponse.json();
    const scoring_result: Record<string, number> = {
      [DEFAULT_QUESTION]: pi_score['total_score'] ?? 0,
    };
    // Extract the request ID
    const requestId = data.request_id;

    // Post the scores to the scoring API.
    const reporting_result = await postScore(
      `https://api.helicone.ai/v1/request/${requestId}/score`,
      scoring_result,
      heliconeApiKey,
    );

    return new Response(JSON.stringify(reporting_result), {
      headers: {
        'Content-Type': 'application/json',
      },
      status: 200,
    });
  } catch (error) {
    console.error('Scoring error:', error);
    return new Response(JSON.stringify({ error: 'Failed to process scoring' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

//Post score data back to Helicone
async function postScore(url: string, scoreData: Record<string, number>, heliconeApiKey: string) {
  const heliconeAuth = `Bearer ${heliconeApiKey}`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: heliconeAuth,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ scores: scoreData }),
    });
    return {
      status: 'Success',
      responseStatusCode: response.status,
      responseBody: await response.json(),
    };
  } catch (e: any) {
    return {
      status: 'Error',
      message: e.message,
    };
  }
}
