from cfnmod.cfnmod import cli


def main():
    cli(auto_envvar_prefix="CFN_MOD")


if __name__ == "__main__":
    main()
