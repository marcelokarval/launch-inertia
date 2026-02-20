/**
 * UserDropdown — Header avatar dropdown with profile/help/logout actions.
 */

import { router } from '@inertiajs/react';
import { Avatar, Dropdown, Button as HeroButton } from '@heroui/react';
import { Settings, HelpCircle, LogOut, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { SidebarUser } from './sidebar-nav-config';

interface Props {
  user: SidebarUser;
}

export function UserDropdown({ user }: Props) {
  const { t } = useTranslation('common');
  return (
    <Dropdown>
      <Dropdown.Trigger>
        <HeroButton
          variant="ghost"
          className="hidden lg:flex items-center gap-2 rounded-lg p-2"
        >
          <Avatar size="sm">
            <Avatar.Fallback className="bg-gradient-primary text-white text-xs font-medium">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </Avatar.Fallback>
          </Avatar>
          <span className="hidden xl:block text-sm font-medium text-foreground truncate max-w-[120px]">
            {user?.name}
          </span>
          <ChevronDown className="h-4 w-4 text-default-400" />
        </HeroButton>
      </Dropdown.Trigger>
      <Dropdown.Popover placement="bottom end">
        <Dropdown.Menu>
          <Dropdown.Item id="profile" onAction={() => router.visit('/app/settings/profile/')}>
            <div className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              <span>{t('nav.profileSettings', 'Profile Settings')}</span>
            </div>
          </Dropdown.Item>
          <Dropdown.Item id="help">
            <div className="flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              <span>{t('nav.helpSupport', 'Help & Support')}</span>
            </div>
          </Dropdown.Item>
          <Dropdown.Item id="logout" onAction={() => router.post('/auth/logout/', {}, { forceFormData: true })}>
            <div className="flex items-center gap-2 text-danger">
              <LogOut className="h-4 w-4" />
              <span>{t('nav.signOut', 'Sign Out')}</span>
            </div>
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown.Popover>
    </Dropdown>
  );
}
