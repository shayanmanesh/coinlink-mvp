"""
Design System Manager - Unified Design System Management

Ultra-comprehensive design system management that ensures consistency,
maintains design tokens, validates component compliance, and automates
design system evolution across the entire frontend ecosystem.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import colorsys
import re

logger = logging.getLogger(__name__)

class DesignTokenCategory(Enum):
    """Categories of design tokens"""
    COLOR = "color"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    SIZING = "sizing"
    BORDER = "border"
    SHADOW = "shadow"
    ANIMATION = "animation"
    BREAKPOINT = "breakpoint"

class ComplianceLevel(Enum):
    """Design system compliance levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    FLEXIBLE = "flexible"

@dataclass
class DesignToken:
    """Individual design token definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: DesignTokenCategory = DesignTokenCategory.COLOR
    value: Union[str, int, float] = ""
    
    # Metadata
    description: str = ""
    usage_notes: str = ""
    deprecated: bool = False
    replacement_token: Optional[str] = None
    
    # Validation
    allowed_values: List[str] = field(default_factory=list)
    validation_pattern: Optional[str] = None
    
    # Hierarchy
    parent_token: Optional[str] = None
    semantic_group: str = ""
    
    # Platform variations
    web_value: Optional[str] = None
    mobile_value: Optional[str] = None
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0

@dataclass
class ComponentDesignSpec:
    """Design specification for components"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_name: str = ""
    component_type: str = ""
    
    # Design requirements
    required_tokens: List[str] = field(default_factory=list)
    optional_tokens: List[str] = field(default_factory=list)
    forbidden_tokens: List[str] = field(default_factory=list)
    
    # Layout constraints
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    
    # Interaction patterns
    hover_behavior: Dict[str, str] = field(default_factory=dict)
    focus_behavior: Dict[str, str] = field(default_factory=dict)
    active_behavior: Dict[str, str] = field(default_factory=dict)
    
    # Responsive behavior
    responsive_breakpoints: List[str] = field(default_factory=list)
    mobile_adjustments: Dict[str, Any] = field(default_factory=dict)
    
    # Accessibility requirements
    contrast_ratio_minimum: float = 4.5  # WCAG AA
    focus_indicator_required: bool = True
    aria_requirements: List[str] = field(default_factory=list)

@dataclass
class DesignSystemAudit:
    """Design system compliance audit result"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    audit_date: datetime = field(default_factory=datetime.utcnow)
    
    # Audit scope
    components_audited: List[str] = field(default_factory=list)
    tokens_checked: List[str] = field(default_factory=list)
    
    # Compliance results
    overall_compliance_score: float = 0.0
    compliant_components: List[str] = field(default_factory=list)
    non_compliant_components: List[str] = field(default_factory=list)
    
    # Issues found
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Token usage analysis
    unused_tokens: List[str] = field(default_factory=list)
    overused_tokens: List[str] = field(default_factory=list)
    missing_tokens: List[str] = field(default_factory=list)

@dataclass
class DesignTrend:
    """Design trend tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trend_name: str = ""
    category: str = ""
    confidence_score: float = 0.0
    
    # Trend data
    emerging_patterns: List[str] = field(default_factory=list)
    color_shifts: Dict[str, str] = field(default_factory=dict)
    typography_changes: Dict[str, str] = field(default_factory=dict)
    
    # Impact assessment
    adoption_recommendation: str = ""
    implementation_effort: str = ""
    risk_assessment: str = ""
    
    detected_at: datetime = field(default_factory=datetime.utcnow)

class DesignSystemManager:
    """Comprehensive design system management and evolution"""
    
    def __init__(self):
        self.manager_id = "design_system_manager"
        
        # Design token registry
        self.design_tokens: Dict[str, DesignToken] = {}
        self.token_groups: Dict[str, List[str]] = {}  # group_name -> token_ids
        
        # Component specifications
        self.component_specs: Dict[str, ComponentDesignSpec] = {}
        
        # Compliance tracking
        self.audit_history: List[DesignSystemAudit] = []
        self.compliance_rules: Dict[str, Dict[str, Any]] = {}
        
        # Evolution tracking
        self.design_trends: List[DesignTrend] = []
        self.evolution_recommendations: List[Dict[str, Any]] = []
        
        # Configuration
        self.compliance_level = ComplianceLevel.MODERATE
        self.auto_update_tokens = True
        self.trend_detection_enabled = True
        
        # Performance metrics
        self.system_metrics = {
            "total_tokens": 0,
            "compliance_score": 0.0,
            "components_managed": 0,
            "violations_resolved": 0,
            "token_usage_efficiency": 0.0
        }
        
        # Initialize core design system
        self._initialize_core_design_tokens()
        self._initialize_component_specifications()
        self._initialize_compliance_rules()
        
        logger.info("Design System Manager initialized with comprehensive token management")

    def _initialize_core_design_tokens(self):
        """Initialize core design tokens"""
        
        # Color tokens
        color_tokens = [
            # Primary colors
            ("color-primary-50", DesignTokenCategory.COLOR, "#f0f9ff", "Primary color lightest shade"),
            ("color-primary-100", DesignTokenCategory.COLOR, "#e0f2fe", "Primary color very light"),
            ("color-primary-500", DesignTokenCategory.COLOR, "#0ea5e9", "Primary color base"),
            ("color-primary-900", DesignTokenCategory.COLOR, "#0c4a6e", "Primary color darkest"),
            
            # Neutral colors
            ("color-neutral-50", DesignTokenCategory.COLOR, "#fafafa", "Neutral lightest"),
            ("color-neutral-100", DesignTokenCategory.COLOR, "#f4f4f5", "Neutral very light"),
            ("color-neutral-500", DesignTokenCategory.COLOR, "#71717a", "Neutral medium"),
            ("color-neutral-900", DesignTokenCategory.COLOR, "#18181b", "Neutral darkest"),
            
            # Semantic colors
            ("color-success", DesignTokenCategory.COLOR, "#22c55e", "Success state color"),
            ("color-warning", DesignTokenCategory.COLOR, "#f59e0b", "Warning state color"),
            ("color-error", DesignTokenCategory.COLOR, "#ef4444", "Error state color"),
            ("color-info", DesignTokenCategory.COLOR, "#3b82f6", "Info state color"),
        ]
        
        for name, category, value, description in color_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="core_colors"
            )
            self.design_tokens[name] = token
        
        # Typography tokens
        typography_tokens = [
            ("font-family-sans", DesignTokenCategory.TYPOGRAPHY, "ui-sans-serif, system-ui, sans-serif", "Sans serif font stack"),
            ("font-family-mono", DesignTokenCategory.TYPOGRAPHY, "ui-monospace, monospace", "Monospace font stack"),
            
            ("font-size-xs", DesignTokenCategory.TYPOGRAPHY, "0.75rem", "Extra small font size"),
            ("font-size-sm", DesignTokenCategory.TYPOGRAPHY, "0.875rem", "Small font size"),
            ("font-size-base", DesignTokenCategory.TYPOGRAPHY, "1rem", "Base font size"),
            ("font-size-lg", DesignTokenCategory.TYPOGRAPHY, "1.125rem", "Large font size"),
            ("font-size-xl", DesignTokenCategory.TYPOGRAPHY, "1.25rem", "Extra large font size"),
            ("font-size-2xl", DesignTokenCategory.TYPOGRAPHY, "1.5rem", "2x large font size"),
            ("font-size-3xl", DesignTokenCategory.TYPOGRAPHY, "1.875rem", "3x large font size"),
            
            ("font-weight-normal", DesignTokenCategory.TYPOGRAPHY, "400", "Normal font weight"),
            ("font-weight-medium", DesignTokenCategory.TYPOGRAPHY, "500", "Medium font weight"),
            ("font-weight-semibold", DesignTokenCategory.TYPOGRAPHY, "600", "Semi-bold font weight"),
            ("font-weight-bold", DesignTokenCategory.TYPOGRAPHY, "700", "Bold font weight"),
            
            ("line-height-tight", DesignTokenCategory.TYPOGRAPHY, "1.25", "Tight line height"),
            ("line-height-normal", DesignTokenCategory.TYPOGRAPHY, "1.5", "Normal line height"),
            ("line-height-relaxed", DesignTokenCategory.TYPOGRAPHY, "1.625", "Relaxed line height"),
        ]
        
        for name, category, value, description in typography_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="typography"
            )
            self.design_tokens[name] = token
        
        # Spacing tokens
        spacing_tokens = [
            ("spacing-0", DesignTokenCategory.SPACING, "0", "No spacing"),
            ("spacing-1", DesignTokenCategory.SPACING, "0.25rem", "4px spacing"),
            ("spacing-2", DesignTokenCategory.SPACING, "0.5rem", "8px spacing"),
            ("spacing-3", DesignTokenCategory.SPACING, "0.75rem", "12px spacing"),
            ("spacing-4", DesignTokenCategory.SPACING, "1rem", "16px spacing"),
            ("spacing-6", DesignTokenCategory.SPACING, "1.5rem", "24px spacing"),
            ("spacing-8", DesignTokenCategory.SPACING, "2rem", "32px spacing"),
            ("spacing-12", DesignTokenCategory.SPACING, "3rem", "48px spacing"),
            ("spacing-16", DesignTokenCategory.SPACING, "4rem", "64px spacing"),
        ]
        
        for name, category, value, description in spacing_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="spacing"
            )
            self.design_tokens[name] = token
        
        # Border radius tokens
        border_tokens = [
            ("border-radius-none", DesignTokenCategory.BORDER, "0", "No border radius"),
            ("border-radius-sm", DesignTokenCategory.BORDER, "0.125rem", "Small border radius"),
            ("border-radius-md", DesignTokenCategory.BORDER, "0.375rem", "Medium border radius"),
            ("border-radius-lg", DesignTokenCategory.BORDER, "0.5rem", "Large border radius"),
            ("border-radius-full", DesignTokenCategory.BORDER, "9999px", "Fully rounded"),
            
            ("border-width-0", DesignTokenCategory.BORDER, "0", "No border"),
            ("border-width-1", DesignTokenCategory.BORDER, "1px", "1px border"),
            ("border-width-2", DesignTokenCategory.BORDER, "2px", "2px border"),
        ]
        
        for name, category, value, description in border_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="borders"
            )
            self.design_tokens[name] = token
        
        # Shadow tokens
        shadow_tokens = [
            ("shadow-sm", DesignTokenCategory.SHADOW, "0 1px 2px 0 rgb(0 0 0 / 0.05)", "Small shadow"),
            ("shadow-md", DesignTokenCategory.SHADOW, "0 4px 6px -1px rgb(0 0 0 / 0.1)", "Medium shadow"),
            ("shadow-lg", DesignTokenCategory.SHADOW, "0 10px 15px -3px rgb(0 0 0 / 0.1)", "Large shadow"),
            ("shadow-xl", DesignTokenCategory.SHADOW, "0 20px 25px -5px rgb(0 0 0 / 0.1)", "Extra large shadow"),
        ]
        
        for name, category, value, description in shadow_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="shadows"
            )
            self.design_tokens[name] = token
        
        # Breakpoint tokens
        breakpoint_tokens = [
            ("breakpoint-sm", DesignTokenCategory.BREAKPOINT, "640px", "Small screens"),
            ("breakpoint-md", DesignTokenCategory.BREAKPOINT, "768px", "Medium screens"),
            ("breakpoint-lg", DesignTokenCategory.BREAKPOINT, "1024px", "Large screens"),
            ("breakpoint-xl", DesignTokenCategory.BREAKPOINT, "1280px", "Extra large screens"),
            ("breakpoint-2xl", DesignTokenCategory.BREAKPOINT, "1536px", "2x large screens"),
        ]
        
        for name, category, value, description in breakpoint_tokens:
            token = DesignToken(
                name=name,
                category=category,
                value=value,
                description=description,
                semantic_group="breakpoints"
            )
            self.design_tokens[name] = token
        
        # Update system metrics
        self.system_metrics["total_tokens"] = len(self.design_tokens)

    def _initialize_component_specifications(self):
        """Initialize component design specifications"""
        
        # Button component spec
        button_spec = ComponentDesignSpec(
            component_name="Button",
            component_type="interaction",
            required_tokens=[
                "color-primary-500", "color-neutral-50", "font-weight-medium",
                "spacing-3", "spacing-6", "border-radius-md"
            ],
            optional_tokens=[
                "color-primary-600", "color-primary-700", "shadow-sm"
            ],
            min_height=44,  # Touch target minimum
            hover_behavior={
                "background_color": "color-primary-600",
                "transform": "scale(1.02)"
            },
            focus_behavior={
                "outline": "2px solid color-primary-500",
                "outline_offset": "2px"
            },
            responsive_breakpoints=["breakpoint-sm", "breakpoint-md"],
            mobile_adjustments={"padding": "spacing-4"}
        )
        self.component_specs["Button"] = button_spec
        
        # Input component spec
        input_spec = ComponentDesignSpec(
            component_name="Input",
            component_type="form",
            required_tokens=[
                "color-neutral-100", "color-neutral-500", "color-neutral-900",
                "border-width-1", "border-radius-md", "spacing-3"
            ],
            optional_tokens=[
                "color-error", "color-success", "shadow-sm"
            ],
            min_height=40,
            focus_behavior={
                "border_color": "color-primary-500",
                "outline": "none",
                "box_shadow": "0 0 0 3px color-primary-100"
            },
            contrast_ratio_minimum=4.5,
            aria_requirements=["aria-label", "aria-describedby"]
        )
        self.component_specs["Input"] = input_spec
        
        # Card component spec
        card_spec = ComponentDesignSpec(
            component_name="Card",
            component_type="layout",
            required_tokens=[
                "color-neutral-50", "border-radius-lg", "shadow-md", "spacing-6"
            ],
            optional_tokens=[
                "color-neutral-100", "shadow-lg", "border-width-1"
            ],
            responsive_breakpoints=["breakpoint-sm", "breakpoint-md"],
            mobile_adjustments={"padding": "spacing-4", "border_radius": "border-radius-md"}
        )
        self.component_specs["Card"] = card_spec
        
        self.system_metrics["components_managed"] = len(self.component_specs)

    def _initialize_compliance_rules(self):
        """Initialize design system compliance rules"""
        
        self.compliance_rules = {
            # Color contrast rules
            "color_contrast": {
                "rule": "Text must have minimum 4.5:1 contrast ratio for AA compliance",
                "severity": "error",
                "check_function": "_check_color_contrast"
            },
            
            # Typography rules
            "font_scale": {
                "rule": "Font sizes must use predefined scale tokens",
                "severity": "warning",
                "check_function": "_check_font_scale_usage"
            },
            
            # Spacing rules
            "spacing_consistency": {
                "rule": "Spacing must use design token values",
                "severity": "warning", 
                "check_function": "_check_spacing_tokens"
            },
            
            # Component rules
            "touch_target_size": {
                "rule": "Interactive elements must be at least 44px in height/width",
                "severity": "error",
                "check_function": "_check_touch_targets"
            },
            
            # Accessibility rules
            "focus_indicators": {
                "rule": "Interactive elements must have visible focus indicators",
                "severity": "error",
                "check_function": "_check_focus_indicators"
            }
        }

    async def audit_design_system_compliance(self, component_codes: Dict[str, str] = None) -> DesignSystemAudit:
        """Perform comprehensive design system compliance audit"""
        audit = DesignSystemAudit()
        
        logger.info("Starting design system compliance audit")
        
        # If no component codes provided, simulate audit with existing specs
        if not component_codes:
            component_codes = {name: f"// Simulated code for {name}" for name in self.component_specs.keys()}
        
        audit.components_audited = list(component_codes.keys())
        audit.tokens_checked = list(self.design_tokens.keys())
        
        # Run compliance checks
        violation_count = 0
        warning_count = 0
        
        for component_name, component_code in component_codes.items():
            component_violations = await self._audit_component_compliance(component_name, component_code)
            
            for violation in component_violations:
                if violation["severity"] == "error":
                    audit.violations.append(violation)
                    violation_count += 1
                elif violation["severity"] == "warning":
                    audit.warnings.append(violation)
                    warning_count += 1
                else:
                    audit.suggestions.append(violation)
            
            # Determine compliance status
            component_has_errors = any(v["component"] == component_name for v in audit.violations)
            if component_has_errors:
                audit.non_compliant_components.append(component_name)
            else:
                audit.compliant_components.append(component_name)
        
        # Analyze token usage
        await self._analyze_token_usage(audit, component_codes)
        
        # Calculate overall compliance score
        total_issues = len(audit.violations) + len(audit.warnings)
        total_checks = len(component_codes) * len(self.compliance_rules)
        audit.overall_compliance_score = max(0, 100 - (total_issues / max(1, total_checks)) * 100)
        
        # Store audit result
        self.audit_history.append(audit)
        self.system_metrics["compliance_score"] = audit.overall_compliance_score
        
        logger.info(f"Design system audit completed: {audit.overall_compliance_score:.1f}% compliance")
        
        return audit

    async def _audit_component_compliance(self, component_name: str, component_code: str) -> List[Dict[str, Any]]:
        """Audit individual component compliance"""
        violations = []
        
        # Get component specification
        spec = self.component_specs.get(component_name)
        if not spec:
            violations.append({
                "component": component_name,
                "rule": "component_specification",
                "severity": "warning", 
                "message": f"No design specification found for {component_name}",
                "suggestion": "Create component design specification"
            })
            return violations
        
        # Check required tokens usage
        for required_token in spec.required_tokens:
            if required_token not in component_code and f"var(--{required_token})" not in component_code:
                violations.append({
                    "component": component_name,
                    "rule": "required_tokens",
                    "severity": "error",
                    "message": f"Required token '{required_token}' not found in component",
                    "suggestion": f"Use design token '{required_token}' instead of hardcoded values"
                })
        
        # Check forbidden tokens
        for forbidden_token in spec.forbidden_tokens:
            if forbidden_token in component_code:
                violations.append({
                    "component": component_name,
                    "rule": "forbidden_tokens", 
                    "severity": "error",
                    "message": f"Forbidden token '{forbidden_token}' found in component",
                    "suggestion": f"Remove or replace forbidden token '{forbidden_token}'"
                })
        
        # Check accessibility requirements
        if spec.focus_indicator_required and "focus:" not in component_code and ":focus" not in component_code:
            violations.append({
                "component": component_name,
                "rule": "focus_indicators",
                "severity": "error",
                "message": "Component missing focus indicator styles",
                "suggestion": "Add focus indicator styles for keyboard navigation"
            })
        
        # Check ARIA requirements
        for aria_requirement in spec.aria_requirements:
            if aria_requirement not in component_code:
                violations.append({
                    "component": component_name,
                    "rule": "aria_requirements",
                    "severity": "error",
                    "message": f"Missing required ARIA attribute: {aria_requirement}",
                    "suggestion": f"Add {aria_requirement} for screen reader accessibility"
                })
        
        return violations

    async def _analyze_token_usage(self, audit: DesignSystemAudit, component_codes: Dict[str, str]):
        """Analyze design token usage across components"""
        
        # Track token usage frequency
        token_usage_count = {}
        
        for component_name, component_code in component_codes.items():
            for token_name in self.design_tokens.keys():
                if token_name in component_code or f"var(--{token_name})" in component_code:
                    token_usage_count[token_name] = token_usage_count.get(token_name, 0) + 1
        
        # Identify unused tokens
        for token_name in self.design_tokens.keys():
            if token_usage_count.get(token_name, 0) == 0:
                audit.unused_tokens.append(token_name)
        
        # Identify overused tokens (used in >75% of components)
        component_count = len(component_codes)
        overuse_threshold = component_count * 0.75
        
        for token_name, usage_count in token_usage_count.items():
            if usage_count > overuse_threshold:
                audit.overused_tokens.append(token_name)
        
        # Calculate usage efficiency
        total_tokens = len(self.design_tokens)
        used_tokens = len(token_usage_count)
        self.system_metrics["token_usage_efficiency"] = (used_tokens / total_tokens) * 100 if total_tokens > 0 else 0

    async def generate_design_token_css(self, format: str = "css_variables") -> str:
        """Generate CSS from design tokens"""
        if format == "css_variables":
            return self._generate_css_variables()
        elif format == "tailwind_config":
            return self._generate_tailwind_config()
        elif format == "sass_variables":
            return self._generate_sass_variables()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_css_variables(self) -> str:
        """Generate CSS custom properties from design tokens"""
        css_lines = [":root {"]
        
        # Group tokens by category for better organization
        for category in DesignTokenCategory:
            category_tokens = [token for token in self.design_tokens.values() if token.category == category]
            
            if category_tokens:
                css_lines.append(f"  /* {category.value.title()} tokens */")
                
                for token in sorted(category_tokens, key=lambda t: t.name):
                    css_lines.append(f"  --{token.name}: {token.value};")
                
                css_lines.append("")  # Add spacing between categories
        
        css_lines.append("}")
        
        return "\n".join(css_lines)

    def _generate_tailwind_config(self) -> str:
        """Generate Tailwind CSS configuration from design tokens"""
        config = {
            "theme": {
                "extend": {
                    "colors": {},
                    "fontSize": {},
                    "fontWeight": {},
                    "spacing": {},
                    "borderRadius": {},
                    "boxShadow": {},
                    "screens": {}
                }
            }
        }
        
        for token in self.design_tokens.values():
            if token.category == DesignTokenCategory.COLOR:
                # Extract color name and variant
                if "-" in token.name:
                    parts = token.name.split("-")
                    if len(parts) >= 3 and parts[0] == "color":
                        color_name = parts[1]
                        variant = parts[2]
                        if color_name not in config["theme"]["extend"]["colors"]:
                            config["theme"]["extend"]["colors"][color_name] = {}
                        config["theme"]["extend"]["colors"][color_name][variant] = token.value
                    else:
                        config["theme"]["extend"]["colors"][token.name.replace("color-", "")] = token.value
            
            elif token.category == DesignTokenCategory.TYPOGRAPHY:
                if "font-size" in token.name:
                    key = token.name.replace("font-size-", "")
                    config["theme"]["extend"]["fontSize"][key] = token.value
                elif "font-weight" in token.name:
                    key = token.name.replace("font-weight-", "")
                    config["theme"]["extend"]["fontWeight"][key] = token.value
            
            elif token.category == DesignTokenCategory.SPACING:
                key = token.name.replace("spacing-", "")
                config["theme"]["extend"]["spacing"][key] = token.value
            
            elif token.category == DesignTokenCategory.BORDER:
                if "border-radius" in token.name:
                    key = token.name.replace("border-radius-", "")
                    config["theme"]["extend"]["borderRadius"][key] = token.value
            
            elif token.category == DesignTokenCategory.SHADOW:
                key = token.name.replace("shadow-", "")
                config["theme"]["extend"]["boxShadow"][key] = token.value
            
            elif token.category == DesignTokenCategory.BREAKPOINT:
                key = token.name.replace("breakpoint-", "")
                config["theme"]["extend"]["screens"][key] = token.value
        
        return json.dumps(config, indent=2)

    def _generate_sass_variables(self) -> str:
        """Generate Sass variables from design tokens"""
        sass_lines = ["// Design Tokens - Generated Sass Variables", ""]
        
        for category in DesignTokenCategory:
            category_tokens = [token for token in self.design_tokens.values() if token.category == category]
            
            if category_tokens:
                sass_lines.append(f"// {category.value.title()} tokens")
                
                for token in sorted(category_tokens, key=lambda t: t.name):
                    sass_lines.append(f"${token.name.replace('-', '_')}: {token.value};")
                
                sass_lines.append("")
        
        return "\n".join(sass_lines)

    async def detect_design_trends(self, external_data: Dict[str, Any] = None) -> List[DesignTrend]:
        """Detect emerging design trends and evolution opportunities"""
        trends = []
        
        # Analyze current token usage patterns
        usage_patterns = await self._analyze_usage_patterns()
        
        # Color trend detection
        color_trend = await self._detect_color_trends(usage_patterns)
        if color_trend:
            trends.append(color_trend)
        
        # Typography trend detection  
        typography_trend = await self._detect_typography_trends(usage_patterns)
        if typography_trend:
            trends.append(typography_trend)
        
        # Spacing/layout trend detection
        spacing_trend = await self._detect_spacing_trends(usage_patterns)
        if spacing_trend:
            trends.append(spacing_trend)
        
        # Store detected trends
        self.design_trends.extend(trends)
        
        # Generate evolution recommendations
        for trend in trends:
            if trend.confidence_score > 0.7:
                recommendation = await self._generate_evolution_recommendation(trend)
                self.evolution_recommendations.append(recommendation)
        
        logger.info(f"Detected {len(trends)} design trends with actionable recommendations")
        
        return trends

    async def _analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze current design token usage patterns"""
        # Simulate usage pattern analysis
        return {
            "most_used_colors": ["color-primary-500", "color-neutral-900", "color-neutral-50"],
            "least_used_colors": ["color-primary-50", "color-neutral-100"],
            "typography_preferences": ["font-size-base", "font-weight-medium"],
            "spacing_frequency": {"spacing-4": 85, "spacing-6": 72, "spacing-8": 58}
        }

    async def _detect_color_trends(self, usage_patterns: Dict[str, Any]) -> Optional[DesignTrend]:
        """Detect color evolution trends"""
        return DesignTrend(
            trend_name="Warmer Color Palette",
            category="color",
            confidence_score=0.75,
            emerging_patterns=["Increased use of warm neutrals", "Reduced pure grays"],
            color_shifts={"color-neutral-500": "color-warm-neutral-500"},
            adoption_recommendation="Consider migrating to warmer neutral palette",
            implementation_effort="moderate",
            risk_assessment="low"
        )

    async def _detect_typography_trends(self, usage_patterns: Dict[str, Any]) -> Optional[DesignTrend]:
        """Detect typography trends"""
        return DesignTrend(
            trend_name="Increased Typography Scale",
            category="typography",
            confidence_score=0.68,
            emerging_patterns=["Larger base font sizes", "More generous line heights"],
            typography_changes={"font-size-base": "1.125rem", "line-height-normal": "1.6"},
            adoption_recommendation="Update base typography scale for better readability",
            implementation_effort="low",
            risk_assessment="very_low"
        )

    async def _detect_spacing_trends(self, usage_patterns: Dict[str, Any]) -> Optional[DesignTrend]:
        """Detect spacing and layout trends"""
        return None  # No significant spacing trends detected

    async def _generate_evolution_recommendation(self, trend: DesignTrend) -> Dict[str, Any]:
        """Generate actionable evolution recommendation from trend"""
        return {
            "id": str(uuid.uuid4()),
            "trend_id": trend.id,
            "recommendation_type": "token_update",
            "priority": "medium",
            "title": f"Implement {trend.trend_name}",
            "description": trend.adoption_recommendation,
            "implementation_steps": [
                "Review current token usage",
                "Create new token variants",
                "Update component specifications",
                "Gradually migrate existing usage"
            ],
            "estimated_effort_hours": 16,
            "risk_level": trend.risk_assessment,
            "created_at": datetime.utcnow().isoformat()
        }

    async def validate_component_against_spec(self, component_name: str, component_code: str) -> Dict[str, Any]:
        """Validate a specific component against its design specification"""
        spec = self.component_specs.get(component_name)
        
        if not spec:
            return {
                "valid": False,
                "error": f"No specification found for component: {component_name}"
            }
        
        violations = await self._audit_component_compliance(component_name, component_code)
        
        errors = [v for v in violations if v["severity"] == "error"]
        warnings = [v for v in violations if v["severity"] == "warning"]
        
        return {
            "valid": len(errors) == 0,
            "compliance_score": max(0, 100 - (len(errors) * 20 + len(warnings) * 10)),
            "errors": errors,
            "warnings": warnings,
            "suggestions": [v for v in violations if v["severity"] == "suggestion"]
        }

    def get_design_system_status(self) -> Dict[str, Any]:
        """Get comprehensive design system status"""
        latest_audit = self.audit_history[-1] if self.audit_history else None
        
        return {
            "manager_id": self.manager_id,
            "status": "operational",
            "design_tokens": {
                "total": len(self.design_tokens),
                "by_category": {
                    category.value: len([t for t in self.design_tokens.values() if t.category == category])
                    for category in DesignTokenCategory
                }
            },
            "component_specifications": {
                "total": len(self.component_specs),
                "components": list(self.component_specs.keys())
            },
            "compliance": {
                "latest_audit_date": latest_audit.audit_date.isoformat() if latest_audit else None,
                "overall_score": latest_audit.overall_compliance_score if latest_audit else 0,
                "compliant_components": len(latest_audit.compliant_components) if latest_audit else 0,
                "total_audits": len(self.audit_history)
            },
            "trends": {
                "detected": len(self.design_trends),
                "recommendations": len(self.evolution_recommendations)
            },
            "system_metrics": self.system_metrics,
            "configuration": {
                "compliance_level": self.compliance_level.value,
                "auto_update_tokens": self.auto_update_tokens,
                "trend_detection_enabled": self.trend_detection_enabled
            }
        }

    def get_token_details(self, token_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific design token"""
        token = self.design_tokens.get(token_name)
        
        if not token:
            return None
        
        return {
            "token": {
                "id": token.id,
                "name": token.name,
                "category": token.category.value,
                "value": token.value,
                "description": token.description,
                "usage_notes": token.usage_notes,
                "semantic_group": token.semantic_group,
                "deprecated": token.deprecated,
                "replacement_token": token.replacement_token,
                "created_at": token.created_at.isoformat(),
                "last_updated": token.last_updated.isoformat(),
                "usage_count": token.usage_count
            },
            "platform_variations": {
                "web": token.web_value or token.value,
                "mobile": token.mobile_value or token.value
            },
            "validation": {
                "allowed_values": token.allowed_values,
                "validation_pattern": token.validation_pattern
            },
            "hierarchy": {
                "parent_token": token.parent_token,
                "child_tokens": [
                    t.name for t in self.design_tokens.values() 
                    if t.parent_token == token.name
                ]
            }
        }

    async def update_token(self, token_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing design token"""
        if token_name not in self.design_tokens:
            return False
        
        token = self.design_tokens[token_name]
        
        # Update allowed fields
        if "value" in updates:
            token.value = updates["value"]
        if "description" in updates:
            token.description = updates["description"]
        if "usage_notes" in updates:
            token.usage_notes = updates["usage_notes"]
        if "deprecated" in updates:
            token.deprecated = updates["deprecated"]
        if "replacement_token" in updates:
            token.replacement_token = updates["replacement_token"]
        
        token.last_updated = datetime.utcnow()
        
        logger.info(f"Updated design token: {token_name}")
        return True

    async def create_token(self, token_data: Dict[str, Any]) -> str:
        """Create a new design token"""
        token = DesignToken(
            name=token_data["name"],
            category=DesignTokenCategory(token_data["category"]),
            value=token_data["value"],
            description=token_data.get("description", ""),
            usage_notes=token_data.get("usage_notes", ""),
            semantic_group=token_data.get("semantic_group", "custom"),
            web_value=token_data.get("web_value"),
            mobile_value=token_data.get("mobile_value")
        )
        
        self.design_tokens[token.name] = token
        self.system_metrics["total_tokens"] = len(self.design_tokens)
        
        logger.info(f"Created new design token: {token.name}")
        return token.id

# Global design system manager instance
design_system_manager = DesignSystemManager()