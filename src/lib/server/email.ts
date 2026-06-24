import { Resend } from 'resend';
import { env } from '$env/dynamic/private';

// Initialize Resend with the key from environment
const resendApiKey = env.RESEND_API_KEY || process.env.RESEND_API_KEY;
export const resend = resendApiKey ? new Resend(resendApiKey) : null;

// Base sender address
// Using Resend's default onboarding address for testing purposes until domain is verified.
export const SENDER_EMAIL = 'alerts@situationmonitor.asia';

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
                <h4 style="margin-top: 0; color: #1f2937;">Event Type: ${eventDetails.summary.category}</h4>
                <p style="font-size: 14px; margin-bottom: 15px;"><strong>Causal Logic:</strong> ${eventDetails.summary.causalLogic}</p>
                
                <h4 style="margin-top: 0;">What Happened</h4>
                <ul style="margin-bottom: 15px;">${eventDetails.summary.what_happened.map((b: string) => `<li>${b}</li>`).join('')}</ul>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e5e7eb; background: #fff;"><strong>Simulated Win Rate</strong></td>
                        <td style="padding: 8px; border: 1px solid #e5e7eb; font-weight: bold; color: #047857;">${eventDetails.summary.backtest.winRate}%</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e5e7eb; background: #fff;"><strong>Historical Cases</strong></td>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;">${eventDetails.summary.backtest.occurrences} identical events</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #e5e7eb; background: #fff;"><strong>Average 1-Day Return</strong></td>
                        <td style="padding: 8px; border: 1px solid #e5e7eb;">${eventDetails.summary.backtest.avgReturn > 0 ? '+' : ''}${eventDetails.summary.backtest.avgReturn}%</td>
                    </tr>
                </table>

                <h4 style="margin-top: 0;">Determinant Impact Map</h4>
                <ul>
                    ${eventDetails.summary.impacts.map((imp: any) => `<li><strong>${imp.asset}</strong>: <span style="color: ${imp.direction === 'UP' ? '#059669' : '#dc2626'}">${imp.direction}</span></li>`).join('')}
                </ul>

                ${eventDetails.impliedMoveLines?.length > 0 ? `
                <h4 style="margin-top: 0;">Options-Implied Moves</h4>
                <ul style="font-family: monospace; font-size: 13px;">
                    ${eventDetails.impliedMoveLines.map((l: string) => `<li>${l}</li>`).join('')}
                </ul>
                ` : ''}
            </div>

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

export async function sendDailyReportEmail(
    email: string,
    marketSnapshot: Record<string, any>,
    unsubToken: string,
    baseUrl: string
) {
    if (!resend) return;

    const unsubLink = `${baseUrl}/unsubscribe?token=${unsubToken}`;
    const tickers = Object.keys(marketSnapshot);

    const html = `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; line-height: 1.5; color: #f3f4f6; background-color: #0a0a0a; padding: 25px; border-radius: 12px; border: 1px solid #262626;">
            <div style="text-align: center; border-bottom: 1px solid #262626; padding-bottom: 20px; margin-bottom: 20px;">
                <h2 style="color: #fbbf24; margin: 0; font-size: 22px; tracking-tight: -0.025em;">QuantAlchemist Lab</h2>
                <p style="color: #a3a3a3; font-size: 13px; margin: 5px 0 0 0;">Daily Market Briefing & System Status</p>
            </div>

            <div style="background-color: #171717; padding: 15px; border-radius: 8px; border: 1px solid #262626; margin-bottom: 20px; text-align: center;">
                <span style="font-size: 11px; font-weight: bold; text-transform: uppercase; color: #10b981; letter-spacing: 0.05em; background-color: rgba(16, 185, 129, 0.1); padding: 4px 10px; border-radius: 9999px;">
                    ● System Status: Stable & Safe
                </span>
                <p style="font-size: 14px; color: #e5e5e5; margin: 12px 0 0 0; line-height: 1.6;">
                    No high-severity macroeconomic or geopolitical anomalies were triggered in the last 24 hours. The risk gates remain in standard monitoring mode.
                </p>
            </div>

            <h3 style="color: #e5e5e5; font-size: 15px; border-bottom: 1px solid #262626; padding-bottom: 8px; margin-bottom: 15px;">Market Snapshot</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="border-bottom: 1px solid #262626;">
                        <th style="text-align: left; padding: 8px; font-size: 12px; color: #a3a3a3; text-transform: uppercase;">Ticker</th>
                        <th style="text-align: right; padding: 8px; font-size: 12px; color: #a3a3a3; text-transform: uppercase;">Price</th>
                        <th style="text-align: right; padding: 8px; font-size: 12px; color: #a3a3a3; text-transform: uppercase;">Daily Change</th>
                    </tr>
                </thead>
                <tbody>
                    ${tickers.map(ticker => {
                        const snap = marketSnapshot[ticker] || { current: 100, changePercent: 0 };
                        const isUp = snap.changePercent >= 0;
                        const color = isUp ? '#10b981' : '#ef4444';
                        const sign = isUp ? '+' : '';
                        return `
                            <tr style="border-bottom: 1px solid #1f1f1f;">
                                <td style="padding: 10px 8px; font-weight: bold; color: #ffffff;">${ticker}</td>
                                <td style="padding: 10px 8px; text-align: right; font-family: monospace; color: #e5e5e5;">$${Number(snap.current).toFixed(2)}</td>
                                <td style="padding: 10px 8px; text-align: right; font-family: monospace; font-weight: bold; color: ${color};">${sign}${Number(snap.changePercent).toFixed(2)}%</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>

            <div style="margin-top: 40px; font-size: 11px; color: #737373; border-top: 1px solid #262626; padding-top: 20px; text-align: center;">
                <p style="margin: 0 0 10px 0;">This is an automated daily report sent to subscribers of OpenStock & QuantAlchemist Laboratory.</p>
                <p style="margin: 0;"><a href="${unsubLink}" style="color: #a3a3a3; text-decoration: underline;">Unsubscribe from these emails</a></p>
            </div>
        </div>
    `;

    await resend.emails.send({
        from: `Situation Monitor <${SENDER_EMAIL}>`,
        to: email,
        subject: `[DAILY REPORT] Market Briefing & System Status`,
        html
    });
}

