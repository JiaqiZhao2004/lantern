type TextInputProps = {
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete?: string;
  required?: boolean;
};

const TextInput: React.FC<TextInputProps> = ({
  label,
  type = "text",
  value,
  onChange,
  autoComplete,
  required,
}) => {
  return (
    <div style={{ marginBottom: "0.75rem" }}>
      <label
        style={{
          display: "block",
          marginBottom: "0.25rem",
          fontSize: "0.9rem",
          fontWeight: 500,
        }}
      >
        {label}
      </label>
      <input
        type={type}
        value={value}
        required={required}
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          padding: "0.5rem 0.6rem",
          borderRadius: "4px",
          border: "1px solid #ccc",
          fontSize: "0.95rem",
        }}
      />
    </div>
  );
};

export default TextInput;
