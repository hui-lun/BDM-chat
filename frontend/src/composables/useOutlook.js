import { ref } from 'vue'

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

  // function openDraftForm(subject = '', body = '', toEmail = '') {
  //   if (Office.context.mailbox.displayNewMessageForm) {
  //     // Convert text to HTML format
  //     const htmlBody = body.split('\n').map(line => `<p>${line}</p>`).join('')
      
  //     Office.context.mailbox.displayNewMessageForm({
  //       toRecipients: [toEmail],  // Use the provided email from mailInfo
  //       subject: subject || "Draft via displayNewMessageForm",
  //       htmlBody: htmlBody || "<p>Hello from Add-in!</p>"
  //     });
  //   } else {
  //     console.error("This Outlook version does not support displayNewMessageForm.");
  //   }
  // }

  function openDraftForm(body = '') {
  if (Office.context.mailbox?.item?.displayReplyForm) {
    const htmlBody = body.split('\n').map(line => `<p>${line}</p>`).join('');
    Office.context.mailbox.item.displayReplyForm(htmlBody);
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
