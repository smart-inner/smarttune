package show

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"strings"
)

type ShowOptions struct {
	Backend string

	genericclioptions.IOStreams
}

func NewShowOptions(streams genericclioptions.IOStreams) *ShowOptions {
	return &ShowOptions{
		IOStreams: streams,
	}
}

func NewCmdShow(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewShowOptions(streams)
	cmd := &cobra.Command{
		Use:   "show SESSION_NAME --backend=backend",
		Short: "show session detail information",
		Long: `Show session detail information, which include system type, system version, tuning knobs,
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Show(args))
		},
	}
	addShowFlags(cmd, o)

	return cmd
}

func addShowFlags(cmd *cobra.Command, opt *ShowOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "",
		"The backend <ip:port> for smarttune server, such as '127.0.0.1:5000'")
}

func (o *ShowOptions) ShowSession(url string) (string, error) {
	request := make(map[string]string)
	resp, err := http.Get(url, request)
	if err != nil {
		return "", err
	}
	return http.HandleResponse(resp)
}

func (o *ShowOptions) Show(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl show %s --backend=%s'", strings.Join(args, " "), o.Backend))
	}

	url := fmt.Sprintf("http://%s/api/session/show/%s", o.Backend, args[0])
	res, err := o.ShowSession(url)
	if err != nil {
		return err
	}
	var out bytes.Buffer
	if err = json.Indent(&out, []byte(res), "", "    "); err != nil {
		return err
	}
	if _, err = out.WriteTo(o.Out); err != nil {
		return err
	}
	return nil
}
