import { Theme } from '@mui/material';

interface UIComponent {
    name: string;
    type: string;
    parent: string;
    styling: Record<string, any>;
}

export const checkUIConsistency = (theme: Theme, components: UIComponent[]) => {
    const issues: string[] = [];
    
    // Check component styling consistency
    components.forEach(component => {
        // Verify spacing consistency
        if (!isSpacingConsistent(component.styling, theme)) {
            issues.push(`Inconsistent spacing in ${component.name}`);
        }
        
        // Verify color usage
        if (!areColorsValid(component.styling, theme)) {
            issues.push(`Invalid color usage in ${component.name}`);
        }
        
        // Check typography consistency
        if (!isTypographyConsistent(component.styling, theme)) {
            issues.push(`Inconsistent typography in ${component.name}`);
        }
        
        // Verify transitions
        if (!areTransitionsValid(component.styling)) {
            issues.push(`Invalid transitions in ${component.name}`);
        }
    });
    
    return issues;
};

const isSpacingConsistent = (styling: Record<string, any>, theme: Theme) => {
    const validSpacing = [0, 1, 2, 3, 4, 5];
    const spacingProps = ['margin', 'padding', 'gap'];
    
    return spacingProps.every(prop => {
        if (styling[prop]) {
            return validSpacing.includes(styling[prop]);
        }
        return true;
    });
};

const areColorsValid = (styling: Record<string, any>, theme: Theme) => {
    const validColors = [
        'primary',
        'secondary',
        'error',
        'warning',
        'info',
        'success'
    ];
    
    return Object.entries(styling)
        .filter(([key]) => key.includes('color'))
        .every(([_, value]) => validColors.includes(value as string));
};

const isTypographyConsistent = (styling: Record<string, any>, theme: Theme) => {
    const validVariants = [
        'h1',
        'h2',
        'h3',
        'h4',
        'h5',
        'h6',
        'body1',
        'body2',
        'subtitle1',
        'subtitle2'
    ];
    
    return styling.typography ? 
        validVariants.includes(styling.typography) : 
        true;
};

const areTransitionsValid = (styling: Record<string, any>) => {
    const validTransitions = [
        'fade',
        'slide',
        'grow',
        'zoom'
    ];
    
    return styling.transition ? 
        validTransitions.includes(styling.transition) : 
        true;
}; 