import React from 'react';
import { Pressable, Text, View } from 'react-native';

import { canExport, downloadJSON, downloadMarkdown, filename, printPage } from '../lib/export';
import { useLocale } from '../lib/locale';
import { font, radius, space, useTheme } from '../theme';

/**
 * Download / print controls.
 *
 * Rendered only on web: `canExport` is false on iOS and Android, where a blob
 * download has nowhere to go. Hiding the buttons is better than showing ones
 * that do nothing — a dead control in a compliance tool teaches the reader that
 * some of the controls are decorative.
 */
export function ExportBar({
  kind,
  subject,
  json,
  markdown,
}: {
  kind: string;
  subject: string;
  json?: unknown;
  markdown?: () => string;
}) {
  const { c } = useTheme();
  const { t } = useLocale();
  if (!canExport) return null;

  return (
    <View
      accessibilityLabel={`${t('export.label')} — ${t('export.note')}`}
      style={{ flexDirection: 'row', gap: space[2], alignItems: 'center', flexWrap: 'wrap' }}>
        {json !== undefined ? (
          <Button label={t('export.json')}
            onPress={() => downloadJSON(json, filename(kind, subject, 'json'))} />
        ) : null}
        {markdown ? (
          <Button label={t('export.markdown')}
            onPress={() => downloadMarkdown(markdown(), filename(kind, subject, 'md'))} />
        ) : null}
      <Button label={t('export.print')} onPress={printPage} primary />
    </View>
  );
}

function Button({ label, onPress, primary }:
  { label: string; onPress: () => void; primary?: boolean }) {
  const { c } = useTheme();
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={{
        paddingHorizontal: space[4], paddingVertical: space[2] + 1, borderRadius: radius.md,
        backgroundColor: primary ? c.accentSubtle : c.surface3,
      }}>
      <Text style={{ color: primary ? c.accent : c.textMuted, fontSize: font.size.caption,
        fontWeight: font.weight.medium, fontFamily: font.sans }}>
        {label}
      </Text>
    </Pressable>
  );
}
