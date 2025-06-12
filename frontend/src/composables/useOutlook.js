import { ref } from 'vue'
import { marked } from 'marked'

// Configure marked to preserve line breaks
marked.setOptions({
  breaks: true,  // Convert single line breaks to <br>
  gfm: true      // Enable GitHub Flavored Markdown
})

export function useOutlook(showErrorMessage, query, sendQuery) {
  // Store the latest email content (auto-update on email switch, but do not auto-fill query)
  const latestMailContent = ref('')

  // Each time the mail icon is clicked, fetch the latest email content and send it immediately
  function getMailInfo(item, bodyText) {
    return {
      title: item.subject || '(none)',
      customer: item.from?.displayName || '(none)',
      customerEmail: item.from?.emailAddress || '',
      BDM: item.to?.map(r => r.displayName).join(', ') || '(none)',
      dateTime: item.dateTimeCreated || '(none)',
      body: bodyText
    }
  }

  function handleEmailChange(autoSend = false) {
    const item = Office.context.mailbox?.item;
    if (!item) {
      showErrorMessage("Cannot access email item.");
      return;
    }
    item.body.getAsync("text", (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        const content = result.value.trim();
        if (content) {
          const mailInfo = getMailInfo(item, content);
          // No longer auto-fill query.value; only send when autoSend is true
          if (autoSend) sendQuery(mailInfo); // Pass mailInfo to sendQuery
        } else {
          showErrorMessage("This email body is empty.");
        }
      } else {
        showErrorMessage("Failed to retrieve email body.");
        console.error("getAsync error:", result.error);
      }
    });
  }

  // When switching emails, auto-update latestMailContent, but do not modify query
  function updateLatestMailContent() {
    const item = Office.context.mailbox?.item;
    if (!item) {
      showErrorMessage("Cannot access email item.");
      latestMailContent.value = ''
      return;
    }

    const Title = item.subject || '(none)';
    const Customer = item.from?.displayName || '(none)';
    const BDM = item.to?.map(r => r.displayName).join(', ') || '(none)';
    const dateTime = item.dateTimeCreated || '(none)';

    item.body.getAsync("text", (result) => {
      if (result.status === Office.AsyncResultStatus.Succeeded) {
        const content = result.value.trim();
        if (content) {
          const fullContent = `
            Customer: ${Customer}
            BDM: ${BDM}
            Title: ${Title}
            DateTime: ${dateTime}

            ${content}
          `.trim();
          latestMailContent.value = fullContent;
        } else {
          latestMailContent.value = '';
          showErrorMessage("This email body is empty.");
        }
      } else {
        latestMailContent.value = '';
        showErrorMessage("Failed to retrieve email body.");
        console.error("getAsync error:", result.error);
      }
    });
  }

  function sendEmailContent() {
    if (typeof Office === 'undefined' || !Office.context.mailbox?.item) {
      showErrorMessage("Not inside Outlook add-in environment.")
      return
    }
    handleEmailChange(true)
  }


  function openDraftForm(body = '') {
    if (Office.context.mailbox?.item?.displayReplyForm) {
      // Use marked to convert markdown to HTML format
      const htmlBody = marked.parse(body);
      
      // Add CSS styles to set font
      const styledHtmlBody = `
        <div style="font-family: 'Aptos', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;">
          ${htmlBody}
        </div>
      `;
      
      Office.context.mailbox.item.displayReplyForm(styledHtmlBody);
    } else {
      console.error("This Outlook version does not support displayReplyForm.");
    }
  }

  return {
    handleEmailChange,
    updateLatestMailContent,
    sendEmailContent,
    openDraftForm,
  }
}