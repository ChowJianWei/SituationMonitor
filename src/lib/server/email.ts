import { Resend } from 'resend';
import { env } from '$env/dynamic/private';

// Initialize Resend with the key from environment
const resendApiKey = env.RESEND_API_KEY || process.env.RESEND_API_KEY;
export const resend = resendApiKey ? new Resend(resendApiKey) : null;

// Base sender address
export const SENDER_EMAIL = 'alerts@situation-monitor.com'; // Replace with a verified domain matching the Resend account

export async function sendConfirmationEmail(email: string, token: string, baseUrl: string) {
    if (!resend) {
        console.warn('Resend API key missing, skipping email send.');
        return;
    }

    const confirmLink = `${baseUrl}/confirm?token=${token}`;

    await resend.emails.send({
        from: `Situation Monitor <${SENDER_EMAIL}>`,
        to: email,
        subject: 'Confirm your subscription to Situation Monitor',
        html: `
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Welcome to Situation Monitor!</h2>
                <p>Please confirm your subscription to receive high-signal market impact alerts.</p>
                <div style="margin: 30px 0;">
                    <a href="${confirmLink}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Confirm Subscription
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
            </div>
        `
    });
}

export async function sendAlertEmail(email: string, eventDetails: any, unsubToken: string, baseUrl: string) {
    if (!resend) return;

    const unsubLink = `${baseUrl}/unsubscribe?token=${unsubToken}`;

    // Note: The precise HTML design here will be refined later
    const html = `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.5;">
            <h2 style="color: #111;">${eventDetails.title}</h2>
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <h4 style="margin-top: 0;">What Happened</h4>
                <ul>${eventDetails.summary.what_happened.map((b: string) => `<li>${b}</li>`).join('')}</ul>
                <h4>Why it Matters</h4>
                <ul>${eventDetails.summary.why_it_matters.map((b: string) => `<li>${b}</li>`).join('')}</ul>
            </div>
            
            <p><strong>Affected Markets:</strong> ${eventDetails.sectors?.join(', ')}</p>
            <p><strong>Tickers to Watch:</strong> ${eventDetails.tickers?.join(', ')}</p>

            <div style="margin-top: 40px; font-size: 12px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                <p><em>This is an informational alert and does not guarantee market returns. Not financial advice.</em></p>
                <p><a href="${unsubLink}" style="color: #6b7280; text-decoration: underline;">Unsubscribe from these alerts</a></p>
            </div>
        </div>
    `;

    await resend.emails.send({
        from: `Situation Monitor <${SENDER_EMAIL}>`,
        to: email,
        subject: `[ALERT] ${eventDetails.title}`,
        html
    });
}
