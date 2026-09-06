import { Link } from 'expo-router';
import React from 'react';
import { View } from 'react-native';

import { Body, Hero, Page } from '../components/ui';
import { useLocale } from '../lib/locale';
import { space, useTheme } from '../theme';

export default function NotFound() {
  const { c } = useTheme();
  const { t } = useLocale();
  return (
    <View>
      <Hero title={t('notfound.title')} />
      <Page>
        <Body muted>{t('notfound.body')}</Body>
        <Link href="/" style={{ color: c.accent }}>{t('notfound.back')}</Link>
      </Page>
    </View>
  );
}
