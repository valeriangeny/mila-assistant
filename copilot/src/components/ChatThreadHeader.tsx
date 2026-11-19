'use client';

import { useChatContext } from '@copilotkit/react-ui';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import { shortThreadId } from '@/lib/chat/thread';

type Props = {
  threadId: string;
  onNewThread: () => void;
};

/** CopilotSidebar `Header` — title, thread id, New thread, close. */
export function ChatThreadHeader({ threadId, onNewThread }: Props) {
  const { setOpen, icons, labels } = useChatContext();
  const short = shortThreadId(threadId);
  const truncated = threadId.trim().length > short.length;

  return (
    <div className="copilotKitHeader mila-chat-header">
      <Stack spacing={0.25} sx={{ minWidth: 0, flex: 1, pr: 1 }}>
        <Typography
          component="div"
          variant="subtitle2"
          noWrap
          sx={{ fontWeight: 700, lineHeight: 1.2 }}
        >
          {labels.title}
        </Typography>
        <Typography
          component="div"
          variant="caption"
          noWrap
          title={threadId}
          data-testid="chat-thread-id"
          data-thread-id={threadId}
          sx={{
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            color: 'text.secondary',
            lineHeight: 1.2
          }}
        >
          thread {short}
          {truncated ? '…' : ''}
        </Typography>
      </Stack>
      <div className="copilotKitHeaderControls mila-chat-header-controls">
        <Button
          size="small"
          variant="outlined"
          onClick={onNewThread}
          data-testid="chat-new-thread"
          aria-label="New thread"
          sx={{
            flexShrink: 0,
            py: 0.25,
            px: 1,
            minWidth: 0,
            fontSize: '0.75rem',
            borderColor: 'divider',
            color: 'text.primary',
            bgcolor: 'background.paper',
            '&:hover': { borderColor: 'primary.main', bgcolor: 'background.paper' }
          }}
        >
          New thread
        </Button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Close"
          className="copilotKitHeaderCloseButton"
        >
          {icons.headerCloseIcon}
        </button>
      </div>
    </div>
  );
}

/** Factory so CopilotSidebar gets a stable component type per thread. */
export function createChatThreadHeader(threadId: string, onNewThread: () => void) {
  return function MilaChatThreadHeader() {
    return <ChatThreadHeader threadId={threadId} onNewThread={onNewThread} />;
  };
}
