function PromptLogin() {
    return (
        <div className="PromptLogin">
            Please sign in to view the page
            <br/> <br/> <br/>
            <button>
                <a href="/login"
                    style={{textDecoration: 'none', color: 'black'}}
                >
                    Sign In
                </a>
            </button>
        </div>
    )
}

export default PromptLogin