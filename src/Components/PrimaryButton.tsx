type PrimaryButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  children,
  disabled,
  ...rest
}) => {
  return (
    <button
      {...rest}
      disabled={disabled}
      style={{
        width: "100%",
        marginTop: "0.5rem",
        padding: "0.6rem 0.8rem",
        borderRadius: "4px",
        border: "none",
        fontSize: "0.95rem",
        fontWeight: 500,
        cursor: disabled ? "default" : "pointer",
        backgroundColor: disabled ? "#cccccc" : "#1976d2",
        color: "#ffffff",
      }}
    >
      {children}
    </button>
  );
};

export default PrimaryButton;
