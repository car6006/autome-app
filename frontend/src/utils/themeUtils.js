// Theme utility functions for OPEN AUTO-ME v1

export const isExpeditorsUser = (user) => {
  return user?.email?.includes('@expeditors.com') || false;
};

export const getThemeClasses = (user) => {
  const isExpeditors = isExpeditorsUser(user);
  
  return {
    isExpeditors,
    mainTheme: isExpeditors ? 'expeditors-theme' : '',
    cardClass: isExpeditors ? 'expeditors-card' : 'shadow-2xl border-0 bg-white/80 backdrop-blur-sm',
    headerClass: isExpeditors ? 'expeditors-header' : 'text-center pb-6',
    primaryButton: isExpeditors ? 'expeditors-button-primary' : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white',
    secondaryButton: isExpeditors ? 'expeditors-button-secondary' : 'border-2 border-dashed border-blue-300 hover:border-blue-500',
    accentColor: isExpeditors ? 'expeditors-accent' : 'text-violet-600',
    navClass: isExpeditors ? 'expeditors-nav' : 'bg-gray-100/90 backdrop-blur-md border-t border-gray-200',
    navItemClass: isExpeditors ? 'expeditors-nav-item' : 'text-gray-600',
    inputClass: isExpeditors ? 'expeditors-input' : '',
    badgeClass: isExpeditors ? 'expeditors-badge' : '',
    gradientBg: isExpeditors ? 'expeditors-gradient-bg' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
  };
};

export const getAppTitle = () => {
  return 'OPEN AUTO-ME v1';
};

export const getBrandingElements = (user) => {
  const isExpeditors = isExpeditorsUser(user);
  
  return {
    showLogo: isExpeditors,
    logoPath: '/expeditors-logo.png',
    appTitle: getAppTitle(),
    brandColors: isExpeditors ? {
      primary: '#ea0a2a',
      secondary: '#231f20',
      accent: '#ffffff'
    } : {
      primary: '#3b82f6',
      secondary: '#8b5cf6',
      accent: '#06b6d4'
    }
  };
};