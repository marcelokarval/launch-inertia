import { Head, router } from '@inertiajs/react';
import DashboardLayout from '@/layouts/DashboardLayout';
import { Tabs } from '@heroui/react';
import { Users, Mail, Phone, Monitor, LayoutDashboard } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type {
  IdentityHubTab, IdentityHubCounts, HubOverviewData,
  Pagination, IdentityListItem, EmailChannelListItem,
  PhoneChannelListItem, DeviceListItem, FingerprintListItem,
  HubDomainHint, HubPrefixHint,
} from '@/types';
import {
  HubOverviewTab, HubPeopleTab, HubEmailsTab, HubPhonesTab, HubDevicesTab,
} from './components';

interface Props {
  tab: IdentityHubTab;
  counts: IdentityHubCounts;
  // Overview tab
  overview?: HubOverviewData;
  // People tab
  identities?: IdentityListItem[];
  filters?: { q: string; tag: string | null };
  pagination?: Pagination;
  // Emails tab
  emails?: EmailChannelListItem[];
  domain_hints?: HubDomainHint[];
  // Phones tab
  phones?: PhoneChannelListItem[];
  prefix_hints?: HubPrefixHint[];
  // Devices tab
  devices?: DeviceListItem[];
  fingerprints?: FingerprintListItem[];
}

const EMPTY_PAGINATION: Pagination = { page: 1, per_page: 25, total: 0, pages: 1 };

export default function IdentitiesIndex(props: Props) {
  const { t } = useTranslation();
  const { tab, counts } = props;

  const handleTabChange = (key: React.Key) => {
    router.get('/app/identities/', { tab: String(key) }, { preserveState: false });
  };

  return (
    <DashboardLayout title={t('identities.index.title', 'Identities')}>
      <Head title={t('identities.index.pageTitle', 'Identities')} />

      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground">
          {t('identities.index.title', 'Identities')}
        </h2>
        <p className="text-sm text-default-500">
          {t('identities.hub.subtitle', 'Your audience intelligence hub')}
        </p>
      </div>

      {/* Tabs */}
      <Tabs selectedKey={tab} onSelectionChange={handleTabChange} className="w-full">
        <Tabs.List className="border-b border-divider mb-6">
          <Tabs.Tab id="overview">
            <LayoutDashboard className="w-4 h-4" />
            {t('identities.hub.tabOverview', 'Overview')}
          </Tabs.Tab>
          <Tabs.Tab id="people">
            <Users className="w-4 h-4" />
            {t('identities.hub.tabPeople', 'People')}
            {counts.people > 0 && <TabBadge count={counts.people} />}
          </Tabs.Tab>
          <Tabs.Tab id="emails">
            <Mail className="w-4 h-4" />
            {t('identities.hub.tabEmails', 'Emails')}
            {counts.emails > 0 && <TabBadge count={counts.emails} />}
          </Tabs.Tab>
          <Tabs.Tab id="phones">
            <Phone className="w-4 h-4" />
            {t('identities.hub.tabPhones', 'Phones')}
            {counts.phones > 0 && <TabBadge count={counts.phones} />}
          </Tabs.Tab>
          <Tabs.Tab id="devices">
            <Monitor className="w-4 h-4" />
            {t('identities.hub.tabDevices', 'Devices')}
            {counts.devices > 0 && <TabBadge count={counts.devices} />}
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel id="overview">
          {props.overview && <HubOverviewTab overview={props.overview} counts={counts} />}
        </Tabs.Panel>

        <Tabs.Panel id="people">
          <HubPeopleTab
            identities={props.identities ?? []}
            filters={props.filters ?? { q: '', tag: null }}
            pagination={props.pagination ?? EMPTY_PAGINATION}
          />
        </Tabs.Panel>

        <Tabs.Panel id="emails">
          <HubEmailsTab
            emails={props.emails ?? []}
            domainHints={props.domain_hints ?? []}
            pagination={props.pagination ?? EMPTY_PAGINATION}
          />
        </Tabs.Panel>

        <Tabs.Panel id="phones">
          <HubPhonesTab
            phones={props.phones ?? []}
            prefixHints={props.prefix_hints ?? []}
            pagination={props.pagination ?? EMPTY_PAGINATION}
          />
        </Tabs.Panel>

        <Tabs.Panel id="devices">
          <HubDevicesTab
            devices={props.devices ?? []}
            fingerprints={props.fingerprints ?? []}
          />
        </Tabs.Panel>
      </Tabs>
    </DashboardLayout>
  );
}

function TabBadge({ count }: { count: number }) {
  return (
    <span className="ml-1.5 px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-default-200 text-default-600">
      {count}
    </span>
  );
}
