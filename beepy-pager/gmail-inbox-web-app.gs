// Google Apps Script web app: list recent Gmail inbox messages for the Beepy pager.
// The Beepy polls this every minute (GMAIL_URL in /etc/beepy-pager.conf) and flashes
// the LED green for each new message. Only sender + subject ever leave Google.
// Deploy as a web app: Execute as "Me", Who has access "Anyone". No trigger needed.

const SECRET = 'CHANGE_ME_SECRET'; // must match key= in the Beepy's GMAIL_URL

function doGet(e) {
  if (e.parameter.key !== SECRET) return json({ error: 'forbidden' });

  // since = unix seconds; the Beepy dedupes by id, so overlapping windows are fine.
  const since = Number(e.parameter.since) || Math.floor(Date.now() / 1000) - 600;
  const me = Session.getEffectiveUser().getEmail().toLowerCase();
  const messages = [];

  // Primary tab only: Promotions/Social/Updates mail never pages.
  for (const thread of GmailApp.search(`in:inbox category:primary after:${since}`, 0, 20)) {
    for (const msg of thread.getMessages()) {
      const time = Math.floor(msg.getDate().getTime() / 1000);
      // Skip older messages in the thread and our own replies.
      if (time < since || (me && msg.getFrom().toLowerCase().includes(me))) continue;
      messages.push({ id: msg.getId(), from: msg.getFrom(), subject: msg.getSubject(), time });
    }
  }
  return json({ messages });
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
