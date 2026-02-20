import { Tooltip } from '@heroui/react';
import { Mail, Phone, Fingerprint } from 'lucide-react';

interface ChannelCountsProps {
  emailCount: number;
  phoneCount: number;
  fpCount: number;
}

export function ChannelCounts({ emailCount, phoneCount, fpCount }: ChannelCountsProps) {
  return (
    <div className="flex items-center gap-3">
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Mail className="w-3 h-3" />
            <span>{emailCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Emails</Tooltip.Content>
      </Tooltip>
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Phone className="w-3 h-3" />
            <span>{phoneCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Phones</Tooltip.Content>
      </Tooltip>
      <Tooltip>
        <Tooltip.Trigger>
          <span className="flex items-center gap-1 text-xs text-default-400">
            <Fingerprint className="w-3 h-3" />
            <span>{fpCount}</span>
          </span>
        </Tooltip.Trigger>
        <Tooltip.Content>Devices</Tooltip.Content>
      </Tooltip>
    </div>
  );
}
